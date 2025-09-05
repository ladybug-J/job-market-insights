#!/bin/bash

cd /Users/judity/Desktop/gitlab/job-market-insights/

# Run .py script
source job-env/bin/activate

python dbtools/delete_and_query.py

deactivate

# Push to git
git add jobs.db
git commit -m "Automated database update"
git push