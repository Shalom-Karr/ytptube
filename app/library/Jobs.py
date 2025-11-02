import asyncio
import logging
import uuid
from pathlib import Path
import sqlite3

from app.library.config import Config
from app.library.Events import EventBus, Events
from app.library.ytdlp import YTDLP

LOG = logging.getLogger(__name__)

class Jobs:
    _instance = None

    def __init__(self, connection):
        self.connection = connection
        self.config = Config.get_instance()
        self.download_path = Path(self.config.download_path)
        EventBus.get_instance().subscribe(Events.DOWNLOAD_COMPLETE, self._on_download_complete)
        EventBus.get_instance().subscribe(Events.DOWNLOAD_ERROR, self._on_download_error)

    @classmethod
    def get_instance(cls, connection=None):
        if cls._instance is None:
            if connection is None:
                raise ValueError("Connection must be provided for the first instance")
            cls._instance = Jobs(connection)
        return cls._instance

    def _on_download_complete(self, data):
        job_id = data.get("job_id")
        filepath = data.get("filepath")
        if job_id:
            # store relative path
            relative_filepath = str(Path(filepath).relative_to(self.download_path))
            self.connection.execute(
                "UPDATE jobs SET status = ?, filepath = ? WHERE id = ?",
                ("completed", relative_filepath, job_id)
            )
            self.connection.commit()
            LOG.info(f"Job {job_id} completed.")

    def _on_download_error(self, data):
        job_id = data.get("job_id")
        error = data.get("error")
        if job_id:
            self.connection.execute(
                "UPDATE jobs SET status = ?, error = ? WHERE id = ?",
                ("failed", error, job_id)
            )
            self.connection.commit()
            LOG.error(f"Job {job_id} failed: {error}")

    async def submit_job(self, url):
        job_id = str(uuid.uuid4())
        self.connection.execute(
            "INSERT INTO jobs (id, url, status) VALUES (?, ?, ?)",
            (job_id, url, "pending")
        )
        self.connection.commit()
        asyncio.create_task(self.run_download(job_id, url))
        return job_id

    async def run_download(self, job_id, url):
        self.connection.execute(
            "UPDATE jobs SET status = ? WHERE id = ?",
            ("in-progress", job_id)
        )
        self.connection.commit()
        LOG.info(f"Starting download for job {job_id}")
        try:
            ytdlp = YTDLP(params={'outtmpl': str(self.download_path / '%(title)s.%(ext)s')})
            await asyncio.to_thread(ytdlp.download, [url], {'job_id': job_id})
        except Exception as e:
            EventBus.get_instance().emit(Events.DOWNLOAD_ERROR, {"job_id": job_id, "error": str(e)})

    def get_job_status(self, job_id):
        cursor = self.connection.cursor()
        cursor.execute("SELECT id, status, filepath, error FROM jobs WHERE id = ?", (job_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def attach(self, app):
        app["jobs"] = self
