# mapv/utm.py -*- coding: utf-8 -*-

"""This module implements the formulae to convert latitude, longitude (ϕ,λ) to
UTM coordinates (E,N), as described in:

https://en.wikipedia.org/wiki/Universal_Transverse_Mercator_coordinate_system.
"""

from math import sqrt, sin, cos, atan, cosh, sinh, atanh

# Constants
a = 6_378.137  # equatorial radius in km
inv_f = 298.257_223_563  # inverse flattening
f = 1/inv_f
N0 = 0  # km in the northern hemisphere
k0 = 0.9996
E0 = 500  # km

# Preliminary values
n = f/(2 - f)
A = (a/(1 + n))*(1 + n**2/4 + n**4/64)

α1 = n/2 + 2/3*n**2 + 5/16*n**3
α2 = 13/48*n**2 + - 3/5*n**3
α3 = 61/240*n**3
α = [0, α1, α2, α3]

β1 = n/2 - 2/3*n**2 + 37/96*n**3
β2 = 1/48*n**2 + 1/15*n**3
β3 = 17/480*n**3

δ1 = 2*n - 2/3*n**2 - 2*n**3
δ2 = 7/3*n**2 - 8/5*n**3
δ3 = 56/15*n**3

λ0 = 123

# From latitude, longitude (ϕ,λ) to UTM coordinates (E,N)

# Intermediate values

def t(ϕ):
    # Assuming that tanh(-1) means atanh, the inverse function of tanh, and not
    # 1/tanh.
    V = 2*sqrt(n)/(1 + n)
    return sinh(atanh(sin(ϕ)) - V*atanh(V*sin(ϕ)))

def ξ(ϕ,λ):
    return atan(t(ϕ)/cos(λ - λ0))

def η(ϕ,λ):
    return atanh(sin(λ - λ0)/sqrt(1 + t(ϕ)**2))

def σ_j(ϕ,λ,j):
    return 2*j*α[j]*cos(2*j*ξ(ϕ,λ))*cosh(2*j*η(ϕ,λ))

def σ(ϕ,λ,j):
    return 1 + σ_j(1) + σ_j(2) + σ_j(3)

def τ_j(ϕ,λ,j):
    return 2*j*α[j]*sin(2*j*ξ(ϕ,λ))*sinh(2*j*η(ϕ,λ))

def τ(ϕ,λ,j):
    return τ_j(1) + τ_j(2) + τ_j(3)

# Final formulae

def E_j(ϕ,λ,j):
    return α[j]*cos(2*j*ξ(ϕ,λ))*sinh(2*j*η(ϕ,λ))
    
def E(ϕ,λ):
    return E0 + k0*A*(η(ϕ,λ) + E_j(ϕ,λ,1) + E_j(ϕ,λ,2) + E_j(ϕ,λ,3)) + 500_000

def N_j(ϕ,λ,j):
    return α[j]*sin(2*j*ξ(ϕ,λ))*cosh(2*j*η(ϕ,λ))
    
def N(ϕ,λ):
    return N0 + k0*A*(ξ(ϕ,λ) + N_j(ϕ,λ,1) + N_j(ϕ,λ,2) + N_j(ϕ,λ,3)) + 500_000

# See also https://geodesy.noaa.gov/NCAT/ for convergence and scale factor

# See also https://earth-info.nga.mil/GandG/publications/tm8358.2/TM8358_2.pdf

# Greek alphabet
#  Α α	alpha, άλφα
#  Β β	beta, βήτα
#  Γ γ	gamma, γάμμα
#  Δ δ	delta, δέλτα
#  Ε ε	epsilon, έψιλον
#  Ζ ζ	zeta, ζήτα
#  Η η	eta, ήτα
#  Θ θ	theta, θήτα
#  Ι ι	iota, ιώτα
#  Κ κ	kappa, κάππα
#  Λ λ	la(m)bda, λά(μ)βδα
#  Μ μ	mu, μυ
#  Ν ν	nu, νυ
#  Ξ ξ	xi, ξι
#  Ο ο	omicron, όμικρον
#  Π π	pi, πι
#  Ρ ρ	rho, ρώ
#  Σ σ	sigma, σίγμα
#  Τ τ	tau, ταυ
#  Υ υ	upsilon, ύψιλον
#  Φ ϕ	phi, ϕι
#  Χ χ	chi, χι
#  Ψ ψ	psi, ψι
#  Ω ω	omega, ωμέγα

def show_data(place, data):
    print(place)
    for i in range(4):
        ϕ = data[i][1]
        λ = data[i][2]
        print(f'{data[i][0]} {ϕ:>3.2f} {λ:>3.2f} {E(ϕ,λ):>6.2f}  {N(ϕ,λ):>7.2f}')
    
#===============================================================================
# main
#===============================================================================

if __name__ == '__main__':
    data = (
        # (ϕ,λ) for SW, NW, NE, SE
        # DLG-3 files write latitude, longitude, easting, northing
        ('SW', 37.75, -122.75),
        ('NW', 38.00, -122.75),
        ('NE', 38.00, -122.50),
        ('SE', 37.75, -122.50)
    )
    show_data('San Francisco', data)
    
    data = (
        # (ϕ,λ) for SW, NW, NE, SE
        # DLG-3 files write latitude, longitude, easting, northing
        ('SW', 34.25, -119.75),
        ('NW', 34.50, -119.75),
        ('NE', 34.50, -119.50),
        ('SE', 34.25, -119.50)
    )
    show_data('Santa Barbara', data)
