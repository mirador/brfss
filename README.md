## Behavioral Risk Factor and Surveillance System (BRFSS) Dataset

These scripts download the BRFSS data provided by [HHS VizRisk](http://www.hhsvizrisk.org/) 
and format it as a mirador project.

### DEPENDENCIES

The scripts have the following dependencies:

1. Python 2.7.3+ (not tested with 3+) and the following package:
  * Requests: http://docs.python-requests.org/en/latest/index.html 

### Usage

**1)** Download and extract the zip files:

```bash
python download.py
```

**2)** Convert the data into Mirador format, specifying the year (either 2011 or 2012):


```bash
python makedataset.py 2011
```

The resulting Mirador datasets will be available inside the mirador folder.