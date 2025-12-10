# PINN Input Data

This directory is designed to **Convert Copernicus Marine data into input data** for the Physics-Informed Neural Network

## Features

- Creates a black and write matrix representing the oil spills at a given instant

---

## How to Use

1. **Open `main.py`**

2. **Configure the Fetching Parameters**
   In `main.py`, you can (have to) adjust manually the following parameters:

   - **Random Data Generation in Circles**:
     - `n_dots_per_circle`: Number of points per circle
     - `n_circles`: Total number of circles
     - `radius_max`: Maximum radius for the circles

   - **DBSCAN Clustering**:
     - `eps`: Maximum distance between two samples for them to be considered as in the same neighborhood

   - **Matrix Framing and Resolution**:
     - `step`: Controls the **size/resolution** of the output matrix (smaller step → higher resolution)
     - `padding_rate`: Value between `0` and `0.49`; acts as a **zoom** level by adding padding around the data


3. **Run the Script**  
   To execute the data fetch, simply run:

   ```bash
   python main.py
