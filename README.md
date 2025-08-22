# CS-340 Project Two: Grazioso Salvare Dashboard

## Overview
The Grazioso Salvare Dashboard is an interactive web-based application for visualizing data from the **Austin Animal Center Outcomes dataset**.  
It was developed as part of **CS-340: Client/Server Development** at Southern New Hampshire University.

The dashboard allows users to:
- Filter animal records by type (Dog, Cat, Rabbit, etc.).
- View detailed information about animals in a data table.
- Select an animal to view its location on an interactive map.

This project integrates:
- **MongoDB** as the backend database (Model).
- **Python Dash** for the dashboard front-end (View/Controller).
- A custom **CRUD Python module** (`animal_shelter.py`) to handle database operations.

---

## Functional Requirements

### Data Table
- Displays animal shelter data (animal type, breed, age, outcome type, etc.).
- Supports interactive filtering by animal type.
- Allows row selection; selecting a row updates the geolocation map.

### Geolocation Map
- Displays Austin, TX and surrounding areas.
- Shows markers for selected animals.
- Each marker includes a tooltip (breed) and a popup (animal name).

### Filter
- Dropdown menu for filtering animals by type.
- Updates both the data table and map dynamically.

---

## Proof of Functionality
Screenshots (in original submission) demonstrated:
- Dashboard with Data Table and Map.
- Filtering animals by type.
- Geolocation markers updating based on row selection.

---

## Tools Used

### MongoDB
- **Role:** Model layer, storing animal shelter outcome data.  
- **Advantages:**  
  - *Scalability* for large datasets.  
  - *Flexible schema* for JSON-like documents.  
  - *Python integration* with `pymongo`.

### Dash Framework
- **Role:** View + Controller for the dashboard.  
- **Advantages:**  
  - Easy to build interactive apps in Python.  
  - Includes components like `dash_table.DataTable` and `dcc.Dropdown`.  
  - Integrates seamlessly with Plotly for visualizations (via `dash_leaflet` for maps).

### Additional Tools
- **pandas** for data cleaning and preparation.  
- **dash_leaflet** for map integration.  

---

## Steps Taken to Complete the Project

1. **Database Setup**  
   - Connected to MongoDB with `pymongo`.  
   - Wrote a **CRUD Python module** (`animal_shelter.py`):contentReference[oaicite:2]{index=2} to handle database operations.  

2. **Data Cleaning and Preparation**  
   - Used pandas to handle missing/malformed latitude/longitude.  
   - Ensured coordinates were numeric for plotting.  

3. **Building the Dashboard**  
   - Created layout with `dash_table.DataTable` and `dcc.Dropdown`.  
   - Integrated logo and styled layout for clarity.  

4. **Adding Interactivity**  
   - Callback #1: filtered the table by selected animal type.  
   - Callback #2: updated the map marker when a row was selected.  

5. **Testing and Debugging**  
   - Verified dropdown filtering.  
   - Ensured maps updated correctly on row selection.  
   - Fixed issues with missing coordinates and integration.

---

## Challenges Encountered and Solutions

- **Missing Coordinates**  
  - Problem: Some records lacked valid latitude/longitude.  
  - Solution: Cleaned data with pandas, dropping invalid rows.

- **Data Table not Updating**  
  - Problem: Dropdown filter initially didn’t update the table.  
  - Solution: Implemented a Dash callback to re-query and update dynamically.

- **Map Integration Issues**  
  - Problem: Linking selected table rows to map markers.  
  - Solution: Used `dash_leaflet` with callbacks to update marker position and info.

---

## Repository Structure
CS340-ProjectTwo-AnimalShelterDashboard/
│
├── ProjectTwoDashboard_Completed.ipynb # Final Jupyter Notebook
├── mod7_project2.py # Python script version of the dashboard
├── animal_shelter.py # CRUD Python module for MongoDB
├── README_project2.docx # Original project writeup (Word format)
└── README.md # This file (portfolio reflection + overview)


---

## Author
**Emmalie Cole**  
Bachelor of Science in Computer Science (Software Engineering)  
Southern New Hampshire University  

---

