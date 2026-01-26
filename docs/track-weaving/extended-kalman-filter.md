# Extended Kalman Filter (EKF) Track Weaver

## Contents
1. [Overview](#overview)
2. [Usage](#usage)
3. [Next Steps](#next-steps)

## Overview

Kalman filters are a powerful tool used in a wide range of applications to estimate the state of a system based on noisy
or incomplete measurements. They work by combining a mathematical model of the system with a series of measurements
taken over time. The model describes how the system's state is expected to evolve, while the measurements provide noisy
observations of the system's actual state. The Kalman filter uses these two sources of information to produce an optimal
estimate of the system's state at each point in time.

The Kalman filter operates recursively, meaning it updates its estimate of the system's state at each time step based on
the previous estimate and the latest measurement. The filter's algorithm consists of two main steps: prediction and
correction. In the prediction step, the filter uses the model to predict the system's state at the next time step based
on the current estimate. In the correction step, the filter uses the latest measurement to correct the prediction and
produce a new estimate of the system's state.

One of the key advantages of Kalman filters is their ability to handle noise and uncertainty. The filter's algorithm
takes into account the statistical properties of the noise in the measurements and the uncertainty in the model. This
allows the filter to produce estimates that are more accurate than those based on a single measurement alone.

The standard Kalman filter assumes that the system's dynamics and the measurement process are linear. However, many
real-world systems are nonlinear. In these cases, the Extended Kalman Filter (EKF) can be used. The EKF is an extension
of the standard Kalman filter that can handle nonlinear systems. It works by linearizing the system's dynamics and the
measurement process around the current estimate of the system's state. This linearization is done using the Jacobian
matrix, which is a matrix of partial derivatives that describes how the system's output changes with respect to its
input.

The EKF is a widely used tool in many applications, including navigation, robotics, and control systems. However, it has
some limitations. The linearization process can introduce errors, especially if the system is highly nonlinear or the
measurements are very noisy. In these cases, other nonlinear filtering techniques, such as the Unscented Kalman Filter
or the Particle Filter, may be more appropriate.

> [!Help]
> Check out some of the resources below for more about the Kalman and Extended Kalman filters:
> - [Kalman filters explained](https://thekalmanfilter.com/kalman-filter-explained-simply/)
> - [An Introduction to the Kalman Filter](https://www.bzarg.com/p/how-a-kalman-filter-works-in-pictures/)
> - [FilterPy Kalman & Bayesian filter examples](https://github.com/rlabbe/Kalman-and-Bayesian-Filters-in-Python?tab=readme-ov-file)
> - [The Math Behind Extended Kalman Filtering](https://medium.com/@sasha_przybylski/the-math-behind-extended-kalman-filtering-0df981a87453)

### Application to Track Weaving

For the track weaving problem, we've attempted to implement the EKF algorithm to correlate incoming radar points to
define a single smoothed-out track as outlined in the problem statement.
Using the [Filterpy](https://filterpy.readthedocs.io/en/latest/index.html) library, we got an initial implementation
that mostly works. The following subsections outline the major milestones and challenges we faced.

#### Milestone 1: Initial working implementation
Since the data being fed to the Kalman filter is assumed to be from GPS, the initial state vector for the filter
consisted of only the point coordinates. We also considered including estimated velocity, heading, and altitude in the
state vector but determined that the extra complexity wasn't strictly necessary for an initial implementation. Because
of this simplified state vector, the state transition, covariance, measurement noise, and process noise matrices were
set to identity matrices. The point weight was included as a divisor in the Kalman filter update step in the measurement
and process noise matrix calculations.

#### Milestone 2: Further simplifications
Upon further development, including the point weight in the noise matrices seemed detrimental so all references were
removed and replaced with hard-coded float defaults. Additionally, the jacobian and measurement function H(x) was set
to return an identity matrix and the first dim_z elements of x, respectively, where dim_z represents the dimension of
the measurement vector. This provided major gains in noise reduction on the output.

#### Milestone 3: Improvements to the model
The next iteration of the Kalman filter lifecycle improved greatly upon earlier versions. The main difference comes from
further updates to the noise matrix calculations. The process noise matrix was updated from an identity to one returned
by FilterPy's `Q_discrete_white_noise` function, which could incorporate the time delta between points. Additionally,
point weight values were reintroduced in the measurement noise matrix calculation.

#### Milestone 4: Final improvements
The latest version improves on how the point weight is used in the measurement noise calculation. Previously, the weight
was used as a multiplier along with a default measurement noise. This penalizes the higher weight points from the EKF
perspective since the noise is higher. Upon this realization, point weight has become a divisor to the matrix
calculation, thereby penalizing low-weight points. To prevent divide-by-zero errors, a very small number—a large power
of the measurement noise—is used when the point weight is zero.

## Usage
Using the EKF Track Weaver is much like using the Time-binned Track Weaver. The Geospatial Controller is responsible for
getting new ATOMS observations using the audit log, creating a Point model from each observation, storing the Points in
the local DB, and finally creating a Track after a configurable time has elapsed from the last observation of a given
node ID.

### Configuration
Currently, the EKF Track Weaver uses the following default values:
- **Measurement noise**: 0.001
- **Process noise**: 0.01
- **X Dimension**: 2
- **Z Dimension**: 2

These can values be overridden through the `config` dictionary argument on `EKFTrackWeaver` instantiation.

The resulting tracks are not published to ATOMS but form the inputs for the various SenseMakers to analyze. In the near term,
we're going to include the ATOMS observation IDs of all the inputs to track weaver with its output tracks so that SenseMakers
can publish relationships between their findings and the original observations. We can also include the TrackWeaver algorithm
used for each input track as an attribute of the resulting findings for transparency.

## Next Steps
Our first pass at the EKF TrackWeaver implementation involved just looking at the incoming latitude and longitude of the
points and associating them with the given confidence scores of the source.  Here are our recommendations for the next
iteration(s) and different ideas to explore:

- Use the given speed and heading of the points to better approximate the points' position given all the incoming data.
- Potentially explore other filters (e.g. Particle Filters or see how a simple alpha-beta filter could be fitted to the problem)
- Build our own model of the state space that specializes in track prediction/smoothing.
