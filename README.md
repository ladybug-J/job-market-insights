## Job Market Insights Dashboard  

⚠️ App still under construction!

### Link to app
https://job-market-insights.streamlit.app

### Overview  
The goal of this project is to build a dashboard that provides deeper insights into the European job market. By default, Indeed and Glassdoor are scraped using the following search terms: _'Data Scientist'_, _'Data Analyst'_, _'AI Engineer'_, in the following countries: _'Austria'_, _'France'_, _'Germany'_, _'Spain'_, _'Switzerland'_.

### Workflow  
1. **Data Collection**:  
   - Scrape job listings using the open-source library **JobSpy**.  
   - Clean the data by removing duplicate ads, removing markdown formatting, and translating job descriptions into 
     English for posterior analysis.
   - Store the processed data in a **SQLite database**.  

2. **Data Analysis & Visualization**:
   - **Time-series of job postings per search term and country** - compare which search term gives better results and visualize trends.
   - **Language used in the job description** - check which search terms are more commonly posted in English.  
   - **Map visualizations** - visualize job location distributions.

3. **Use of Large Language Models (LLMs) to extract structured information from description**: _(In progress)_ \\
   Job descriptions contain more detailed unstructured information about the field where the search term is applied, and the requirements for the position (as proficiency in tools, frameworks, devices, languages...). For extracting this information without hardcoding keywords or guessing semantic structures, open source LLMs are leveraged during the preprocessing of the data. With this information, better insights of the most demanded skills can be extracted, useful for example when thinking about taking a course about a cloud platform.

    \-\-\- Challenges \-\-\-
       - The LLM has to run locally, as streamlit cloud probably does not have enough resources
       - This implies the ETL should also run locally
       - Scheduling a daily update of the database locally and sending it to git could solve the problem


