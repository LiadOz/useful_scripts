import json
import subprocess


JOB_FILE = 'clalit_jobs.json'
LAST_JOB_FILE = 'clalit_user_previous_job.json'


def get_jobs(from_previous_jobs=False):
    file = JOB_FILE
    if from_previous_jobs:
        file = LAST_JOB_FILE
    try:
        with open(file, 'r') as f:
            return json.loads(f.read())
    except FileNotFoundError:
        return []


def add_job(chat_id, job_data):
    jobs = get_jobs()
    for job in jobs:
        if job['chat_id'] == chat_id:
            return 'You already have a schedule entry'
    job_data['chat_id'] = chat_id
    jobs.append(job_data)
    with open(JOB_FILE, 'w') as f:
        json.dump(jobs, f)

    add_job_to_previous_jobs(chat_id, job_data=job_data)


def add_job_to_previous_jobs(chat_id, job_data):
    previous_jobs = get_jobs(True)
    found_job = False
    for job in previous_jobs:
        if job['chat_id'] == chat_id:
            for k, v in job_data.items():
                job[k] = v
                found_job = True
    if not found_job:
        previous_jobs.append(job_data)
    with open(LAST_JOB_FILE, 'w') as f:
        json.dump(previous_jobs, f)


def get_previous_job(chat_id):
    previous_jobs = get_jobs(True)
    for job in previous_jobs:
        if job['chat_id'] == chat_id:
            return job
    return None


def remove_entry(chat_id):
    jobs = get_jobs()
    new_jobs = list(filter(lambda x: x['chat_id'] != chat_id, jobs))
    with open(JOB_FILE, 'w') as f:
        json.dump(new_jobs, f)


def server_is_up():
    ps_result = subprocess.getstatusoutput('ps aux | grep clalit')
    processes = ps_result[1].split('\n')
    if len(processes) > 2:
        return True
    return False


def verify_job_msg(msg):
    if not msg.get('clinic_id'):
        return 'missing clinic_id field'
    if not msg.get('doctor_code'):
        return 'missing doctor_code field'
