# job_finder_cli
A **Command Line Interface (CLI)** built with **Typer** to interact with the [itjobs.pt](https://itjobs.pt) API.   The tool allows you to **search, filter, and analyze job offers**, extract **salary info**, and enrich data with **AmbitionBox** and **Indeed**.   Results can be exported to CSV for further analysis.  

# Features

-  **Clean HTML descriptions** (remove tags from job descriptions)  
- **List N most recent jobs** (sorted by publication date)  
- **Filter full-time jobs** by company & location  
-  **Extract salaries** (from `wage` field or regex in description)  
-  **Filter jobs by skills and date range**  
-  **Enrich job info** with AmbitionBox & Indeed (rating, benefits, company description)  
-  **Statistics** (vacancies per title/location)  
-  **Export results** to CSV  

# Examples
# 1. List the 5 most recent jobs
python job_finder_cli.py listar-n-trabalhos 5

# 2. Filter 3 Full-time jobs from "Accenture" in "Lisboa"
python job_finder_cli.py full-time-emp "Accenture" "Lisboa" 3

# 3. Extract salary info for job ID 12345
python job_finder_cli.py salary 12345

# 4. Find jobs requiring Python + SQL between two dates
python job_finder_cli.py skills --skill Python --skill SQL 2025-01-01 2025-03-01

# 5. Get enriched job info with AmbitionBox
python job_finder_cli.py get-job-info 12345

# 6. Generate job statistics (vacancies per title/location)
python job_finder_cli.py statistics

# 7. List top 10 skills for a job title (from AmbitionBox)
python job_finder_cli.py list-skills "Data Scientist"
