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

