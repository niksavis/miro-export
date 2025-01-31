import argparse
import requests
import time
import os
import uuid
import json


def make_miro_request(method, url, access_token, params=None, json_data=None):
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.request(
            method=method, url=url, headers=headers, params=params, json=json_data
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        error_data = e.response.json()
        print(f"\nAPI Error: {error_data.get('status')} - {error_data.get('code')}")
        print(f"Request URL: {url}")
        print("Full error response:")
        print(json.dumps(error_data, indent=2))  # Pretty-print JSON
        exit(1)


def create_export_job(access_token, org_id, board_ids, board_format="SVG"):
    url = f"https://api.miro.com/v2/orgs/{org_id}/boards/export/jobs"
    request_id = str(uuid.uuid4())
    params = {"request_id": request_id}
    payload = {
        "boardIds": board_ids,
        "boardFormat": board_format,
    }
    print(f"Created export job with request ID: {request_id}")
    return make_miro_request(
        "POST", url, access_token, params=params, json_data=payload
    )


def get_job_status(access_token, org_id, job_id):
    url = f"https://api.miro.com/v2/orgs/{org_id}/boards/export/jobs/{job_id}"
    return make_miro_request("GET", url, access_token)


def get_export_results(access_token, org_id, job_id):
    url = f"https://api.miro.com/v2/orgs/{org_id}/boards/export/jobs/{job_id}/results"
    return make_miro_request("GET", url, access_token)


def download_file(url, output_path):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"Download failed: {str(e)}")
        return False


def main(args=None):
    parser = argparse.ArgumentParser(description="Export Miro boards")
    parser.add_argument(
        "-t", "--access-token", required=True, help="Bearer access token"
    )
    parser.add_argument("-g", "--org-id", required=True, help="Organization ID")
    parser.add_argument(
        "-b", "--board-ids", nargs="+", required=True, help="Space-separated board IDs"
    )
    parser.add_argument(
        "-f",
        "--board-format",
        choices=["SVG", "HTML", "PDF"],
        default="SVG",
        help="Export format (SVG, HTML, PDF) - default: SVG",
    )
    parser.add_argument(
        "-o",
        "--output-folder",
        default="archive",
        help="Output directory - default: archive",
    )

    args = parser.parse_args(args)

    os.makedirs(args.output_folder, exist_ok=True)

    # Step 1: Create export job
    print("Creating export job...")
    try:
        job_data = create_export_job(
            args.access_token, args.org_id, args.board_ids, args.board_format
        )
        job_id = job_data["jobId"]
        print(f"Created job ID: {job_id}")
    except SystemExit:
        exit(1)

    # Step 2: Poll job status
    print(f"Tracking job status (ID: {job_id})...")
    while True:
        status_data = get_job_status(args.access_token, args.org_id, job_id)
        if status_data["jobStatus"] == "FINISHED":
            break
        if status_data["jobStatus"] in ["FAILED", "CANCELLED"]:
            print(f"Job failed with status: {status_data['jobStatus']}")
            exit(1)
        print("Job still processing, waiting 5 minutes...")
        time.sleep(300)  # 5 minutes

    # Step 3: Get export results
    print("Fetching export results...")
    results = get_export_results(args.access_token, args.org_id, job_id)

    # Step 4: Download files
    success_count = 0
    for result in results["results"]:
        if result["status"] == "SUCCESS" and result["exportLink"]:
            filename = f"{result['boardId']}.zip"
            output_path = os.path.join(args.output_folder, filename)
            if download_file(result["exportLink"], output_path):
                print(f"Downloaded: {output_path}")
                success_count += 1
            else:
                print(f"Failed to download: {result['boardId']}")

    print(
        f"\nJob {job_id} completed. Downloaded {success_count} files to: {os.path.abspath(args.output_folder)}"
    )
    exit(0)


if __name__ == "__main__":
    main()
