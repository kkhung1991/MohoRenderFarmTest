"""Slave client for distributed rendering."""
import json
import os
import shutil
import socket
import tempfile
import threading
import time
import zipfile
import zlib
from pathlib import Path
from typing import Optional, Callable, Dict, Tuple, List
import requests
from src.moho_renderer import RenderJob, MohoRenderer, RenderStatus


def _crc32_file(path, chunk_size=1024 * 1024):
    """Compute the unsigned CRC32 of a file (matches zip CRC), or None on error."""
    try:
        crc = 0
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                crc = zlib.crc32(chunk, crc)
        return crc & 0xFFFFFFFF
    except OSError:
        return None


class SlaveClient:
    """Connects to a master server and processes render jobs."""

    # Video output extensions, for versioned (timestamped) output filenames
    _VIDEO_EXT = {"MP4": ".mp4", "QT": ".mov", "M4V": ".m4v", "AVI": ".avi",
                  "ASF": ".asf", "MOV": ".mov", "Animated GIF": ".gif", "GIF": ".gif"}

    def __init__(self, master_host: str, master_port: int, moho_path: str,
                 slave_port: int = 0, max_concurrent: int = 1):
        self.master_host = master_host
        self.master_port = master_port
        self.moho_path = moho_path
        self.slave_port = slave_port
        self.hostname = socket.gethostname()
        self._max_concurrent = max(1, max_concurrent)
        self._running = False
        self._workers: List[threading.Thread] = []
        self._heartbeat_thread = None
        self._lock = threading.Lock()
        self._active_renders: Dict[int, Tuple[MohoRenderer, RenderJob]] = {}
        self.completed_jobs: List[RenderJob] = []
        self._force_update_triggered = False
        self.render_enabled = True  # Whether this slave accepts render jobs
        self.farm_renders_dir = ""  # Where farm renders go (empty = default)
        self.sync_dir = ""  # Persistent local folder for incremental file sync (empty = off)
        self.sync_prune = False  # Delete previously-synced files no longer in the project
        self.version_output = False  # Add a timestamp to farm output (don't overwrite)
        self.last_transfer = {}  # Latest transfer/sync status (for local display)
        self._last_transfer_report = 0.0

        # Callbacks
        self.on_connected: Optional[Callable[[], None]] = None
        self.on_disconnected: Optional[Callable[[], None]] = None
        self.on_job_started: Optional[Callable[[RenderJob], None]] = None
        self.on_job_completed: Optional[Callable[[RenderJob], None]] = None
        self.on_output: Optional[Callable[[str], None]] = None
        self.on_status_changed: Optional[Callable[[str], None]] = None
        self.on_force_update: Optional[Callable[[], None]] = None

    @property
    def master_url(self):
        return f"http://{self.master_host}:{self.master_port}"

    @property
    def is_running(self):
        return self._running

    @property
    def current_jobs(self) -> list:
        """Return list of all currently rendering jobs."""
        with self._lock:
            return [job for _, job in self._active_renders.values()]

    def start(self):
        """Start the slave client with concurrent workers."""
        if self._running:
            return
        self._running = True
        mode = "render+submit" if self.render_enabled else "submit-only"
        if self.on_output:
            self.on_output(f"Starting slave ({mode} mode, {self._max_concurrent} workers)")
        self._workers = []
        for i in range(self._max_concurrent):
            t = threading.Thread(target=self._worker_loop, args=(i,), daemon=True)
            self._workers.append(t)
            t.start()
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()

    def stop(self):
        """Stop the slave client and cancel all active renders."""
        if self.on_output:
            with self._lock:
                active = len(self._active_renders)
            self.on_output(f"Stopping slave ({active} active render{'s' if active != 1 else ''})")
        self._running = False
        with self._lock:
            for renderer, _ in self._active_renders.values():
                renderer.cancel()
        for t in self._workers:
            t.join(timeout=10)
        self._workers = []

    def _register(self) -> bool:
        """Register with the master server."""
        try:
            resp = requests.post(
                f"{self.master_url}/api/register",
                json={
                    "hostname": self.hostname,
                    "port": self.slave_port,
                    "render_enabled": self.render_enabled,
                },
                timeout=5,
            )
            if resp.status_code == 200:
                if self.on_connected:
                    self.on_connected()
                if self.on_output:
                    mode = "render+submit" if self.render_enabled else "submit-only"
                    self.on_output(f"Registered with master at {self.master_host}:{self.master_port} [{mode}]")
                return True
        except requests.ConnectionError:
            if self.on_output:
                self.on_output(f"Cannot connect to master at {self.master_host}:{self.master_port}")
        except Exception as e:
            if self.on_output:
                self.on_output(f"Registration error: {e}")
        return False

    def _heartbeat_loop(self):
        """Send periodic heartbeats to master."""
        while self._running:
            try:
                with self._lock:
                    active_count = len(self._active_renders)
                status = "rendering" if active_count > 0 else "idle"
                resp = requests.post(
                    f"{self.master_url}/api/heartbeat",
                    json={
                        "port": self.slave_port,
                        "status": status,
                        "active_jobs": active_count,
                        "render_enabled": self.render_enabled,
                    },
                    timeout=5,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for job_id in data.get("cancel_jobs", []):
                        self._cancel_active_job(job_id)
                    if data.get("force_update") and not self._force_update_triggered:
                        self._force_update_triggered = True
                        if self.on_output:
                            self.on_output("Master requested force update, checking...")
                        threading.Thread(target=self._handle_force_update, daemon=True).start()
            except Exception:
                pass
            time.sleep(10)

    def _handle_force_update(self):
        """Check for update, download+stage, then signal GUI to restart."""
        try:
            from src.updater import check_for_update, download_and_stage_update
            from src.config import APP_VERSION

            new_version = check_for_update(APP_VERSION)
            if not new_version:
                if self.on_output:
                    self.on_output("Already up to date, no update needed")
                self._force_update_triggered = False
                return

            if self.on_output:
                self.on_output(f"Update v{new_version} found, downloading...")

            success = download_and_stage_update(
                on_progress=lambda msg: self.on_output(msg) if self.on_output else None
            )

            if success:
                if self.on_output:
                    self.on_output(f"Update v{new_version} staged, restarting...")
                if self.on_force_update:
                    self.on_force_update()
            else:
                if self.on_output:
                    self.on_output("Update download failed")
                self._force_update_triggered = False
        except Exception as e:
            if self.on_output:
                self.on_output(f"Force update error: {e}")
            self._force_update_triggered = False

    def _cancel_active_job(self, job_id: str):
        """Cancel a specific active render by job ID (requested by master)."""
        with self._lock:
            for worker_id, (renderer, job) in self._active_renders.items():
                if job.id == job_id:
                    if self.on_output:
                        self.on_output(f"Cancelling job by master request: {job.project_name}")
                    job.status = RenderStatus.CANCELLED.value
                    renderer.cancel()
                    return

    def _worker_loop(self, worker_id: int):
        """Worker loop: request and process jobs from master."""
        registered = False
        while self._running:
            if not registered:
                registered = self._register()
                if not registered:
                    time.sleep(5)
                    continue

            # Skip job requests when rendering is disabled (submit-only mode)
            if not self.render_enabled:
                time.sleep(3)
                continue

            # Request a job
            try:
                resp = requests.get(
                    f"{self.master_url}/api/get_job",
                    params={"port": self.slave_port},
                    timeout=10,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    job_data = data.get("job")
                    if job_data:
                        job = RenderJob.from_dict(job_data)
                        if self.on_output:
                            files_flag = " [with files]" if job.farm_files_uploaded else ""
                            self.on_output(f"Worker {worker_id}: Received job from master: {job.project_name} [{job.id}]{files_flag}")
                        self._process_job(worker_id, job)
                    else:
                        time.sleep(3)
                elif resp.status_code == 403:
                    if self.on_output:
                        self.on_output(f"Worker {worker_id}: Not registered, re-registering...")
                    registered = False
                    time.sleep(2)
                else:
                    if self.on_output:
                        self.on_output(f"Worker {worker_id}: Unexpected response from master: HTTP {resp.status_code}")
                    time.sleep(5)
            except requests.ConnectionError:
                registered = False
                if self.on_disconnected:
                    self.on_disconnected()
                if self.on_output:
                    self.on_output(f"Worker {worker_id}: Lost connection to master, reconnecting...")
                time.sleep(5)
            except Exception as e:
                if self.on_output:
                    self.on_output(f"Worker {worker_id} error: {e}")
                time.sleep(5)

    def _report_transfer(self, force=False, min_interval=1.0, **fields):
        """Report this slave's transfer/sync status to the master (throttled,
        best-effort) and cache it locally for display."""
        now = time.time()
        if not force and (now - self._last_transfer_report) < min_interval:
            return
        self._last_transfer_report = now
        cached = dict(fields)
        cached["updated"] = now
        self.last_transfer = cached
        try:
            payload = {"port": self.slave_port}
            payload.update(fields)
            requests.post(f"{self.master_url}/api/transfer_progress",
                          json=payload, timeout=3)
        except Exception:
            pass

    def _resolve_render_file(self, job: RenderJob):
        """Best-effort path to the single rendered video file for a job, or None
        (e.g. for image-sequence formats which aren't single files)."""
        ext = self._VIDEO_EXT.get(job.format)
        if not ext or not job.output_path:
            return None
        p = Path(job.output_path)
        if p.suffix:
            return p
        return p / (Path(job.project_file).stem + ext)

    def _upload_render(self, worker_id: int, job: RenderJob):
        """Upload a finished video to the master so it can be reviewed there."""
        f = self._resolve_render_file(job)
        if not f or not f.exists():
            return
        try:
            size_mb = f.stat().st_size / (1024 * 1024)
            self._report_transfer(force=True, phase="uploading", project=job.project_name,
                                  bytes_total=f.stat().st_size, bytes_done=0)
            if self.on_output:
                self.on_output(f"Worker {worker_id}: Uploading render to master: "
                               f"{f.name} ({size_mb:.1f} MB)")
            with open(str(f), "rb") as fh:
                resp = requests.post(f"{self.master_url}/api/upload_render/{job.id}",
                                     files={"render": (f.name, fh, "application/octet-stream")},
                                     timeout=1800)
            if self.on_output:
                if resp.status_code == 200:
                    self.on_output(f"Worker {worker_id}: Render uploaded to master: {f.name}")
                else:
                    self.on_output(f"Worker {worker_id}: Render upload failed: HTTP {resp.status_code}")
        except Exception as e:
            if self.on_output:
                self.on_output(f"Worker {worker_id}: Render upload error: {e}")

    def _process_job(self, worker_id: int, job: RenderJob):
        """Process a single render job."""
        # Pre-warm / sync-only job: cache files locally, don't render
        if job.sync_only:
            self._process_sync_only(worker_id, job)
            return

        work_dir = None
        persistent_workdir = False  # True when work_dir is the reusable sync folder

        # Obtain project files from master if needed
        if job.farm_files_uploaded:
            # Prefer incremental sync into the persistent client folder.
            if self.sync_dir:
                work_dir = self._sync_files(worker_id, job,
                                            Path(self.sync_dir).expanduser(), persistent=True)
                if work_dir is not None:
                    persistent_workdir = True
            # No persistent cache: per-file sync into a temp dir (works for
            # folder-backed jobs that have no zip), else legacy full-zip download.
            if work_dir is None:
                tmp = Path(tempfile.mkdtemp(prefix=f"moho_farm_{job.id}_"))
                work_dir = self._sync_files(worker_id, job, tmp, persistent=False)
                if work_dir is None:
                    shutil.rmtree(str(tmp), ignore_errors=True)
                    work_dir = self._download_and_extract_files(worker_id, job)
            if work_dir is None:
                job.status = RenderStatus.FAILED.value
                job.error_message = "Failed to obtain project files from master"
                self._report_completion(job)
                self.completed_jobs.append(job)
                if self.on_job_completed:
                    self.on_job_completed(job)
                return

        # Farm jobs with uploaded files render from a temp dir, and the
        # submitter's output_path points at the SUBMITTER's filesystem
        # (a different user/host) which isn't writable here. Always redirect
        # output to this slave's local farm renders folder.
        if job.farm_files_uploaded:
            from src.config import DEFAULT_FARM_RENDERS_DIR
            renders_dir = self.farm_renders_dir or DEFAULT_FARM_RENDERS_DIR
            name = Path(job.project_file).stem
            if self.version_output:
                # Timestamped name so re-renders don't overwrite the previous one
                ts = time.strftime("%Y%m%d_%H%M%S")
                ext = self._VIDEO_EXT.get(job.format)
                if ext:
                    job.output_path = os.path.join(renders_dir, f"{name}_{ts}{ext}")
                else:
                    job.output_path = os.path.join(renders_dir, f"{name}_{ts}")
            elif job.subfolder_project:
                job.output_path = os.path.join(renders_dir, name)
            else:
                job.output_path = renders_dir
            try:
                os.makedirs(renders_dir, exist_ok=True)
            except OSError as e:
                job.status = RenderStatus.FAILED.value
                job.error_message = f"Cannot create farm renders folder '{renders_dir}': {e}"
                if self.on_output:
                    self.on_output(f"Worker {worker_id}: ERROR: {job.error_message}")
                self._report_completion(job)
                if work_dir and not persistent_workdir:
                    self._cleanup_work_dir(work_dir, job)
                self.completed_jobs.append(job)
                if self.on_job_completed:
                    self.on_job_completed(job)
                return
            if self.on_output:
                self.on_output(f"Worker {worker_id}: Farm output -> {job.output_path}")

        renderer = MohoRenderer(self.moho_path)
        with self._lock:
            self._active_renders[worker_id] = (renderer, job)

        if self.on_job_started:
            self.on_job_started(job)
        if self.on_output:
            self.on_output(f"Worker {worker_id}: Processing job: {job.project_name}")
        if self.on_status_changed:
            with self._lock:
                count = len(self._active_renders)
            self.on_status_changed(f"rendering ({count} active)")

        self._report_transfer(force=True, phase="rendering", project=job.project_name,
                              render_pct=0)
        renderer.render(
            job,
            on_output=self.on_output,
            on_progress=lambda p: self._report_transfer(
                phase="rendering", project=job.project_name, render_pct=p),
        )
        self._report_transfer(force=True, phase="idle", project=job.project_name)

        with self._lock:
            self._active_renders.pop(worker_id, None)

        # Post-render: auto-compose layer comps with ffmpeg
        if (job.status == RenderStatus.COMPLETED.value
                and job.compose_layers and job.layercomp):
            try:
                from src.ffmpeg_compose import compose_layer_comps
                out_dir = Path(job.output_path).parent if job.output_path else Path(job.project_file).parent
                if self.on_output:
                    self.on_output(f"Worker {worker_id}: Starting ffmpeg layer composition...")
                compose_layer_comps(str(out_dir), on_output=self.on_output,
                                    reverse_order=job.compose_reverse_order)
            except Exception as e:
                if self.on_output:
                    self.on_output(f"Worker {worker_id}: FFmpeg compose error: {e}")

        # Upload the finished video to the master for review (best-effort)
        if job.status == RenderStatus.COMPLETED.value:
            self._upload_render(worker_id, job)

        # Report completion
        self._report_completion(job)

        # Cleanup temp files (but keep the persistent sync folder for reuse)
        if work_dir and not persistent_workdir:
            self._cleanup_work_dir(work_dir, job)

        self.completed_jobs.append(job)

        if self.on_job_completed:
            self.on_job_completed(job)
        if self.on_status_changed:
            with self._lock:
                count = len(self._active_renders)
            status = f"rendering ({count} active)" if count > 0 else "idle"
            self.on_status_changed(status)

    def _process_sync_only(self, worker_id: int, job: RenderJob):
        """Pre-warm: sync the job's files into the persistent sync folder and
        report completion without rendering."""
        if self.on_job_started:
            self.on_job_started(job)

        synced = False
        if job.farm_files_uploaded and self.sync_dir:
            synced = self._sync_files(worker_id, job,
                                      Path(self.sync_dir).expanduser(), persistent=True) is not None

        if self.on_output:
            if synced:
                self.on_output(f"Worker {worker_id}: Pre-sync complete — "
                               f"files cached, no render")
            elif not self.sync_dir:
                self.on_output(f"Worker {worker_id}: Pre-sync skipped — "
                               f"no Client Sync Folder set on this machine")
            else:
                self.on_output(f"Worker {worker_id}: Pre-sync could not cache files")

        job.status = RenderStatus.COMPLETED.value
        job.progress = 100.0
        self._report_completion(job)  # master cleans its uploaded bundle on completion
        self.completed_jobs.append(job)
        if self.on_job_completed:
            self.on_job_completed(job)
        if self.on_status_changed:
            with self._lock:
                count = len(self._active_renders)
            self.on_status_changed(f"rendering ({count} active)" if count > 0 else "idle")

    def _report_completion(self, job: RenderJob):
        """Report job completion to master."""
        success = job.status == RenderStatus.COMPLETED.value
        cancelled = job.status == RenderStatus.CANCELLED.value
        if self.on_output:
            if success:
                elapsed = job.elapsed_str if hasattr(job, 'elapsed_str') else "?"
                self.on_output(f"Job completed: {job.project_name} ({elapsed}) - reporting to master")
            elif cancelled:
                self.on_output(f"Job cancelled: {job.project_name} - reporting to master")
            else:
                self.on_output(f"Job failed: {job.project_name} ({job.error_message}) - reporting to master")
        try:
            requests.post(
                f"{self.master_url}/api/job_complete",
                json={
                    "port": self.slave_port,
                    "job_id": job.id,
                    "success": success,
                    "cancelled": cancelled,
                    "error": job.error_message,
                },
                timeout=10,
            )
        except Exception as e:
            if self.on_output:
                self.on_output(f"Error reporting job completion: {e}")

    def _download_and_extract_files(self, worker_id: int, job: RenderJob):
        """Download project bundle from master and extract to temp dir."""
        work_dir = Path(tempfile.mkdtemp(prefix=f"moho_farm_{job.id}_"))
        zip_path = work_dir / f"{job.id}.zip"

        try:
            if self.on_output:
                self.on_output(f"Worker {worker_id}: Downloading files for {job.project_name}...")

            resp = requests.get(
                f"{self.master_url}/api/download_files/{job.id}",
                timeout=300, stream=True,
            )
            if resp.status_code != 200:
                if self.on_output:
                    self.on_output(f"Worker {worker_id}: File download failed: HTTP {resp.status_code}")
                shutil.rmtree(str(work_dir), ignore_errors=True)
                return None

            total = int(resp.headers.get("Content-Length", 0))
            done = 0
            last_pct = -10
            start = time.time()
            self._report_transfer(force=True, phase="downloading", project=job.project_name,
                                  files_total=1, files_done=0,
                                  bytes_total=total, bytes_done=0, speed_bps=0)
            with open(str(zip_path), "wb") as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    f.write(chunk)
                    done += len(chunk)
                    elapsed = time.time() - start
                    speed = done / elapsed if elapsed > 0 else 0
                    self._report_transfer(phase="downloading", project=job.project_name,
                                          files_total=1, files_done=0,
                                          bytes_total=total, bytes_done=done, speed_bps=speed)
                    if total > 0 and self.on_output:
                        pct = int(done * 100 / total)
                        if pct >= last_pct + 10:
                            last_pct = pct
                            self.on_output(
                                f"Worker {worker_id}: Downloading... {pct}% "
                                f"({done / 1024 / 1024:.1f}/{total / 1024 / 1024:.1f} MB)")
            self._report_transfer(force=True, phase="idle", project=job.project_name,
                                  bytes_total=total, bytes_done=done, speed_bps=0)

            size_mb = zip_path.stat().st_size / (1024 * 1024)
            if self.on_output:
                self.on_output(f"Worker {worker_id}: Downloaded {size_mb:.1f} MB, extracting...")

            with zipfile.ZipFile(str(zip_path), "r") as zf:
                file_count = len(zf.namelist())
                zf.extractall(str(work_dir))
            zip_path.unlink()

            if self.on_output:
                self.on_output(f"Worker {worker_id}: Extracted {file_count} files to {work_dir}")

            # Rewrite job project path to extracted location
            original_name = job.farm_original_project or Path(job.project_file).name
            new_project = work_dir / original_name
            if new_project.exists():
                job.project_file = str(new_project)
                if self.on_output:
                    self.on_output(f"Worker {worker_id}: Project file: {new_project}")
            else:
                if self.on_output:
                    self.on_output(f"Worker {worker_id}: WARNING: Expected project file not found: {new_project}")

            return work_dir
        except Exception as e:
            if self.on_output:
                self.on_output(f"Worker {worker_id}: Download error: {e}")
            shutil.rmtree(str(work_dir), ignore_errors=True)
            return None

    def _sync_files(self, worker_id: int, job: RenderJob, sync_root, persistent=True):
        """Incrementally sync a job's files into sync_root using the master's
        manifest (path/size/CRC): only missing or changed files are downloaded.

        Works for both folder-backed and zip-backed jobs (the master serves a
        manifest + per-file downloads for both). When persistent is True the
        folder is treated as a reusable cache (change detection + prune state);
        otherwise it's a one-shot temp target. Returns sync_root, or None to
        fall back (e.g. manifest unavailable on an older master).
        """
        sync_root = Path(sync_root).expanduser()
        try:
            sync_root.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            if self.on_output:
                self.on_output(f"Worker {worker_id}: Cannot use sync folder {sync_root}: {e}")
            return None

        # Fetch the file manifest for this job
        try:
            resp = requests.get(f"{self.master_url}/api/file_manifest/{job.id}", timeout=60)
            if resp.status_code != 200:
                if self.on_output:
                    self.on_output(f"Worker {worker_id}: Manifest unavailable "
                                   f"(HTTP {resp.status_code}); doing full download")
                return None
            files = resp.json().get("files", [])
        except Exception as e:
            if self.on_output:
                self.on_output(f"Worker {worker_id}: Manifest error ({e}); doing full download")
            return None

        if not files:
            if self.on_output:
                self.on_output(f"Worker {worker_id}: Empty manifest; doing full download")
            return None

        # Determine which files need downloading (missing / size or CRC mismatch)
        to_download = []
        for entry in files:
            rel = entry.get("path", "")
            if not rel:
                continue
            target = sync_root / rel
            if (target.is_file()
                    and target.stat().st_size == entry.get("size")
                    and _crc32_file(target) == entry.get("crc")):
                continue
            to_download.append(entry)

        reused = len(files) - len(to_download)
        if self.on_output:
            self.on_output(f"Worker {worker_id}: Sync: {len(files)} files, "
                           f"{len(to_download)} to update, {reused} reused")

        total_bytes = sum(e.get("size", 0) for e in to_download)
        cached_bytes_total = sum(e.get("size", 0) for e in files)
        done_bytes = 0
        files_done = reused
        last_pct = -10
        start = time.time()
        self._report_transfer(force=True, phase="syncing", project=job.project_name,
                              files_total=len(files), files_done=files_done,
                              bytes_total=total_bytes, bytes_done=0, speed_bps=0)
        for entry in to_download:
            rel = entry["path"]
            target = sync_root / rel
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                r = requests.get(f"{self.master_url}/api/download_file/{job.id}",
                                 params={"path": rel}, timeout=600, stream=True)
                if r.status_code != 200:
                    if self.on_output:
                        self.on_output(f"Worker {worker_id}: Failed to fetch {rel} "
                                       f"(HTTP {r.status_code})")
                    return None
                tmp = target.with_name(target.name + ".part")
                with open(str(tmp), "wb") as f:
                    for chunk in r.iter_content(chunk_size=65536):
                        f.write(chunk)
                        done_bytes += len(chunk)
                        elapsed = time.time() - start
                        speed = done_bytes / elapsed if elapsed > 0 else 0
                        self._report_transfer(phase="syncing", project=job.project_name,
                                              files_total=len(files), files_done=files_done,
                                              bytes_total=total_bytes, bytes_done=done_bytes,
                                              speed_bps=speed)
                        if total_bytes > 0 and self.on_output:
                            pct = int(done_bytes * 100 / total_bytes)
                            if pct >= last_pct + 10:
                                last_pct = pct
                                self.on_output(
                                    f"Worker {worker_id}: Syncing... {pct}% "
                                    f"({done_bytes / 1024 / 1024:.1f}/"
                                    f"{total_bytes / 1024 / 1024:.1f} MB)")
                os.replace(str(tmp), str(target))
                files_done += 1
            except Exception as e:
                if self.on_output:
                    self.on_output(f"Worker {worker_id}: Sync error for {rel}: {e}")
                return None

        elapsed = time.time() - start
        self._report_transfer(force=True, phase="idle", project=job.project_name,
                              files_total=len(files), files_done=len(files),
                              bytes_total=total_bytes, bytes_done=done_bytes,
                              speed_bps=(done_bytes / elapsed if elapsed > 0 else 0),
                              cached_files=len(files), cached_bytes=cached_bytes_total)

        if self.on_output:
            if to_download:
                self.on_output(f"Worker {worker_id}: Sync complete "
                               f"({total_bytes / 1024 / 1024:.1f} MB transferred)")
            else:
                self.on_output(f"Worker {worker_id}: All files already up to date "
                               f"(0 MB transferred)")

        # Record managed files and optionally prune ones no longer in the project
        # (only for the persistent cache, not one-shot temp targets).
        if persistent:
            self._update_sync_state(worker_id, sync_root,
                                    set(e["path"] for e in files if e.get("path")))

        # Point the job at the synced project file
        original = job.farm_original_project or Path(job.project_file).name
        new_project = sync_root / original
        if not new_project.exists():
            if self.on_output:
                self.on_output(f"Worker {worker_id}: Synced project not found "
                               f"({new_project}); doing full download")
            return None
        job.project_file = str(new_project)
        if self.on_output:
            self.on_output(f"Worker {worker_id}: Using synced project: {new_project}")
        return sync_root

    _SYNC_STATE_FILE = ".moho_sync_state.json"

    def _update_sync_state(self, worker_id: int, sync_root: Path, current_paths: set):
        """Persist the set of managed files. When pruning is enabled, delete
        files this slave previously synced that are no longer in the project.

        Only files recorded in our own state file are ever removed, so other
        contents of the sync folder are never touched.
        """
        state_path = sync_root / self._SYNC_STATE_FILE
        previous = set()
        try:
            if state_path.is_file():
                previous = set(json.loads(state_path.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            previous = set()

        if self.sync_prune:
            removed = 0
            for rel in (previous - current_paths):
                p = sync_root / rel
                try:
                    if p.is_file():
                        p.unlink()
                        removed += 1
                        parent = p.parent
                        while (parent != sync_root and parent.is_dir()
                               and not any(parent.iterdir())):
                            parent.rmdir()
                            parent = parent.parent
                except OSError:
                    pass
            if removed and self.on_output:
                self.on_output(f"Worker {worker_id}: Pruned {removed} file(s) "
                               f"no longer in the project")

        try:
            state_path.write_text(json.dumps(sorted(current_paths)), encoding="utf-8")
        except OSError:
            pass

    def _cleanup_work_dir(self, work_dir, job: RenderJob):
        """Clean up temp directory and request master cleanup."""
        if self.on_output:
            self.on_output(f"Cleaning up temp files: {work_dir}")
        try:
            shutil.rmtree(str(work_dir), ignore_errors=True)
        except Exception as e:
            if self.on_output:
                self.on_output(f"Warning: Failed to cleanup temp dir: {e}")
        try:
            requests.delete(
                f"{self.master_url}/api/cleanup_files/{job.id}",
                timeout=10,
            )
            if self.on_output:
                self.on_output(f"Requested master cleanup for job {job.id}")
        except Exception as e:
            if self.on_output:
                self.on_output(f"Warning: Failed to request master cleanup: {e}")

    def submit_job(self, job: RenderJob, bundle_path: str = "") -> bool:
        """Submit a job to the master for rendering by the farm.

        If bundle_path is provided, uploads the file bundle first.
        Returns True if the master accepted the job.
        """
        # Upload file bundle if provided
        if bundle_path and os.path.exists(bundle_path):
            try:
                if self.on_output:
                    size_mb = os.path.getsize(bundle_path) / (1024 * 1024)
                    self.on_output(f"Uploading files for {job.project_name} ({size_mb:.1f} MB)...")
                with open(bundle_path, "rb") as f:
                    resp = requests.post(
                        f"{self.master_url}/api/upload_files/{job.id}",
                        files={"bundle": (f"{job.id}.zip", f, "application/zip")},
                        timeout=300,
                    )
                if resp.status_code != 200:
                    if self.on_output:
                        self.on_output(f"File upload failed: HTTP {resp.status_code}")
                    return False
                if self.on_output:
                    self.on_output(f"Files uploaded for {job.project_name}")
            except Exception as e:
                if self.on_output:
                    self.on_output(f"File upload error: {e}")
                return False
            finally:
                try:
                    os.unlink(bundle_path)
                    if self.on_output:
                        self.on_output(f"Cleaned up local bundle: {bundle_path}")
                except OSError:
                    pass

        # Submit job metadata
        try:
            resp = requests.post(
                f"{self.master_url}/api/add_job",
                json=job.to_dict(),
                timeout=10,
            )
            if resp.status_code == 200:
                if self.on_output:
                    self.on_output(f"Submitted job to master: {job.project_name}")
                return True
            else:
                if self.on_output:
                    self.on_output(f"Master rejected job: HTTP {resp.status_code}")
                return False
        except requests.ConnectionError:
            if self.on_output:
                self.on_output("Cannot submit job: not connected to master")
            return False
        except Exception as e:
            if self.on_output:
                self.on_output(f"Error submitting job: {e}")
            return False
