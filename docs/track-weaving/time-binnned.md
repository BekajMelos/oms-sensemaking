# Time-binned Track Weaver

This document outlines the algorithm(s), configuration, and overall approach to creating a Track Weaver that utilizes 
local time-binning.

## Contents
1. [Overview](#overview)
2. [Algorithm](#algorithm)
3. [Usage](#usage)

## Overview
The current approach first passes individual observations through a common-sense filter for impossible values (right 
now, just altitudes out of range). Then, it bins the observations by detection time using a configurable interval. We 
then perform a weighted average of the observations' lat-lon values within each bin, weighted according to confidence 
level. Points previously filtered for having unrealistic values are assigned a weight of 0 so they don't affect the 
outcome. Finally, the weaved track is run through filtering for extreme changes in altitude or lat-lon to catch bad 
data that was binned together and thus survived averaging.

## Algorithm
First, all input points are sorted in chronological order. Next, they are grouped into bins of configurable size, with
a default of 60 seconds. This process aims to condense duplicate observations from multiple sources of varying quality 
and accuracy into a single point per bin. The Geospatial Controller has already assigned a weight between 0.0 and 1.0 
to each point, based on the OMS observation's confidence attribute. 

Within each group, a new point is generated using a weighted average of all the included points, considering the 
latitude, longitude, and detection time, all weighted by the points' individual weights. The Aggregated Confidence 
Metric (ACM) is created by rolling up the input ACMs, and the confidence value for the new point is set to the lowest 
confidence among the input points. Finally, the new point's weight is calculated as a simple average of the weights 
from the input points. Although this new value is present, it is currently unused, as only one TrackWeaver is run at 
a time.

## Usage
The Geospatial Controller is responsible for getting new OMS observations using the audit log, creating a Point model 
from each observation, storing the Points in the local DB, and finally creating a Track after a configurable time has 
elapsed from the last observation of a given node ID. Point and Track objects are only used internally by SenseMaker 
algorithms and are never stored in OMS. All Points are given an initial weight by the controller based entirely on the 
incoming observation's confidence attribute, although in the future, a global multiplier based on the observation’s 
source or provider could also be applied.

### Configuration
The confidence weights and bin size are configurable through Sensemaker environment variables. The current default 
values are:
- **Bin size**: 60 seconds
- **Low confidence**: 0.25
- **Moderate confidence**: 0.5
- **High confidence**: 1.0
- **Unknown confidence**: 0.5

The resulting tracks are not published to OMS but form the inputs for the various SenseMakers to analyze. In the near 
term, we're going to include the OMS observation IDs of all the inputs to track weaver with its output tracks so that 
SenseMakers can publish relationships between their findings and the original observations. We can also include the 
TrackWeaver algorithm used for each input track as an attribute of the resulting findings for transparency.
