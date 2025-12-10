# oildrift

This project is based on Opendrift, a python framework which allows simulate oil drifting in the ocean (https://opendrift.github.io/index.html)

## Create a virtual environment

A virtual environment is necessary to execute the scripts.
```bash
py -m venv env_name
```

Depending on your operating system, you can now activate your virtual environment. On Windows, for example:
```bash
.\env_name\Scripts\activate
```

After created your virtual environment and activated it, you can install all built-in packages from the `requirements.txt` file using the following command:
```bash
pip install -r requirements.txt
```

You will also need some external packages.
- Opendrift (https://github.com/OpenDrift/opendrift);
- AdiosDB (https://github.com/NOAA-ORR-ERD/adios_oil_database);
- PyNUCOS (https://github.com/NOAA-ORR-ERD/PyNUCOS).

Cloning the Opendrift package, is sufficient, as it will automatically install its dependencies, including the other two packages. Clone it using its HTTPS URL into a `packages` folder for example.
```bash
cd ./packages/
```
```bash
git clone <HTTPS_URL>
```

Navigate to the cloned package folder:
```bash
cd ./opendrift/
```

Install it into your virtual environment (don't forget the final point):
```bash
pip install -e . 
```

## Project Structure & Features

### tecdrift

A program from the beginning of the internship written by Bruno Kassar to start with Opendrift. 


### SimulationGenerator - Completed

A module designed to:

- Run a large number of oil drift simulations
- Use YAML configuration files to define all simulation parameters  
- Study the optimal time step for numerical integration
- Process simulation outputs and compute convergence criteria

---

### PINN (Physics-Informed Neural Networks) - Not Finished

This folder contains scripts used to:

- Transform raw particle positions into grouped structures  
- Represent oil slicks graphically from particle clouds  
- Created in order to prepare data for ML-based or physics-informed modeling  

Useful for building surrogate models or advanced post-processing.