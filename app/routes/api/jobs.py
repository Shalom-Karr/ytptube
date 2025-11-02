from aiohttp import web
from app.library.Jobs import Jobs
from app.library.router import app_route, RouteRegistration

@app_route("/api/submit", method="POST", name="submit_job")
async def submit_job(request: web.Request) -> web.Response:
    data = await request.json()
    url = data.get("url")
    if not url:
        return web.json_response({"error": "URL is required"}, status=400)

    jobs = request.app["jobs"]
    job_id = await jobs.submit_job(url)
    return web.json_response({"job_id": job_id})

@app_route("/api/status/{job_id}", method="GET", name="get_job_status")
async def get_job_status(request: web.Request) -> web.Response:
    job_id = request.match_info["job_id"]
    jobs = request.app["jobs"]
    status = jobs.get_job_status(job_id)
    if not status:
        return web.json_response({"error": "Job not found"}, status=404)
    return web.json_response(status)

def register_routes() -> list[RouteRegistration]:
    return [
        submit_job,
        get_job_status
    ]