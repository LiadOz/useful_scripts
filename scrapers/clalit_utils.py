import json


JOB_FILE = 'clalit_jobs.json'


def get_jobs():
    try:
        with open(JOB_FILE, 'r') as f:
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


def remove_entry(chat_id):
    jobs = get_jobs()
    new_jobs = list(filter(lambda x: x['chat_id'] != chat_id, jobs))
    with open(JOB_FILE, 'w') as f:
        json.dump(new_jobs, f)



def verify_job_msg(msg):
    if not msg.get('clinic_id'):
        return 'missing clinic_id field'
    if not msg.get('doctor_code'):
        return 'missing doctor_code field'
