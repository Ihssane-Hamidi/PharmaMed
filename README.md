# ESG Portfolio Analytics Dashboard

## Overview

This interactive financial dashboard was developed to evaluate portfolio sustainability and financial performance using structured ESG and financial datasets.

The goal is to help investment professionals and green funds make informed decisions by combining ESG indicators with quantitative financial metrics.

The dashboard translates complex data into clear, actionable insights and supports portfolio analysis and monitoring.


## Key Features

- ESG scoring and sustainability indicators visualization  
- Portfolio performance tracking (returns, volatility, risk-adjusted metrics)  
- Risk-adjusted performance metrics (Sharpe ratio, drawdowns, etc.)  
- Interactive filtering and comparison tools  
- Dynamic charts and data visualization  

## Technical Stack

**Core Libraries:**

- Python  
- Pandas (data structuring & transformation)  
- NumPy (numerical computations)  
- yfinance (market data retrieval)  
- requests (API data extraction)  
- openpyxl (Excel integration)  
- Streamlit (interactive dashboard deployment)  

## Data Workflow

1. Data acquisition from APIs and public ESG datasets  
2. Data cleaning, normalization, and structuring  
3. Computation of financial and ESG performance metrics  
4. Integration into an interactive visualization interface  
5. Deployment via Streamlit for live demonstration  

## Architecture

Data acquisition → Data processing → Metric computation → Visualization layer

## What This Project Demonstrates

- Structuring and transforming financial & ESG data  
- Quantitative portfolio analysis  
- Integration of ESG metrics into financial dashboards  
- Deployment of interactive decision-support tools  
- Ability to automate data collection and analysis  

## Live Demo

https://pharmamed-arebm9slkkyommvrapcadi.streamlit.app/

## Screenshot 1:Dashboard main page
  ## Interactive Search Engine
The dashboard features an advanced search engine that allows users to query by:
      - **Medicines**: Denomination, CIS code, or CIP13 code  
      - **Medical Devices**: HAS code or denomination  

Search results provide comprehensive, actionable information including:
- Administration route  
- Format & presentation  
- Request status  
- Type of procedure / approval pathway  
- Commercialization date and commercialization flag  
- Public price & improved price  
- Reimbursement rate  
- SMR or ASMR rating  
- Approval / accreditation by public authorities / collectives  
- Holder(s) / Manufacturer information  

This feature transforms complex regulatory, commercial, and reimbursement data into **instant insights**, enabling healthcare professionals, 
analysts, and fund managers to make informed decisions quickly.

  
## Screenshot 2:Company / Laboratory Analysis

The second page of the dashboard provides in-depth analysis of pharmaceutical companies and laboratories.  

Users can:

- Browse all medicines found in public datasets (BPDM, HAS, Data.gouv)  
- Explore company groups and their subsidiaries  
- Access key indicators for each company/group:  
    - Total number of products  
    - Product breakdown (medicines vs. medical devices)  
    - Best-rated SMR/ASMR products  
- Visualize product distribution via interactive charts and diagrams  
- Analyze SMR/ASMR ratings across the portfolio  
- Compare two companies/groups using a toggle button for side-by-side analysis  

This functionality allows healthcare analysts, fund managers, and researchers to:

- Understand the composition and performance of pharmaceutical groups  
- Identify high-value products or standout ASMR/SMR ratings  
- Quickly benchmark companies for strategic decisions or research purposes  

The page integrates multiple datasets seamlessly and presents **complex, multi-dimensional data** in a clear, interactive format.
 
## Screenshot 3:  Financial Analysis of Pharmaceutical Groups

The third page of the dashboard provides financial insights for pharmaceutical companies, currently covering 10 major groups.  

Features include:

- Revenue breakdown of medicines sold, extracted from publicly available financial reports  
- Interactive histograms showing sales distribution across products and categories  
- Identification of top-selling medicines with detailed information (CIS code, specific presentation)  
- Potential integration of AI models to automatically extract and enrich financial information from annual reports  

This page allows users to:

- Quickly understand the financial performance of pharmaceutical groups  
- Identify key revenue-generating products  
- Compare financial results across multiple companies  
- Visualize data in a clear, interactive, and actionable format  

The dashboard is designed to consolidate complex regulatory, commercial, and financial datasets into a single, **decision-ready interface** for analysts, fund managers, and healthcare researchers.


## Screenshot 4:Portfolio ESG Analysis

The fourth page of the dashboard allows users to upload their own portfolio XLSX files, containing pharmaceutical groups and their respective weightings.  

This feature is designed for investment professionals and ESG-focused funds to:

- Evaluate the **ESG profile** of their portfolio  
- Calculate aggregated regulatory and clinical ratings, including:  
    - SMR  
    - ASMR  
    - ASR  
    - SR  
    - Overall portfolio ESG score  
- Analyze portfolio composition across pharmaceutical groups  
- Visualize weighted ESG and financial metrics interactively
  
The tool provides **instant feedback** on portfolio sustainability and regulatory performance, enabling fund managers to optimize investments for both financial and ESG objectives.  

