"""
fhe_library/context.py

The Context class holds and manages global parameters for the CKKS scheme.
"""
import numpy as np
from typing import List

# Placeholder for a prime generation utility
# In a real scenario, this would be more robust, finding NTT-friendly primes etc.
def _generate_primes_for_educational_purpose(
    poly_degree: int,
    moduli_bits: List[int]
) -> List[int]:
    """
    Generates a list of pseudo-primes for educational purposes.
    This is NOT cryptographically secure or robust prime generation.
    It aims to find numbers that are likely prime and of the specified bit length.
    Real FHE schemes require primes with specific properties (e.g., q = 1 mod 2N for NTT).
    """
    primes = []
    for bits in moduli_bits:
        # Start with a number of the correct bit length
        num = (1 << (bits -1)) + 1
        # Simple odd number search, not a real primality test for FHE
        # This is a placeholder and needs to be replaced with actual prime finding
        # For this educational version, we'll use known small primes or user-provided ones.
        # This function as is will not produce correct primes for FHE.
        # Let's use a fixed set for now if no real prime generation is available.

        # Simplified: For educational purposes, we might expect user to provide primes,
        # or use very specific ones. This function is illustrative of where it would go.
        # For now, let's assume this helper would find actual primes.
        # Example: if bits = 60, find a 60-bit prime.
        # This is a hard problem. We will rely on user-provided primes or fixed examples.
        # For this placeholder, let's return numbers that are just large and odd.
        # This is insufficient for real FHE.
        # Example: 2**bits - some_small_number (if it's prime)

        # Using a simple approach for placeholder: find first prime > 2^(bits-1)
        # This is still computationally intensive if not careful.
        # For now, this function will be a conceptual placeholder.
        # Actual prime values will be provided in examples or by the user.
        if bits == 60:
            primes.append(1152921504606846899) # A known 60-bit prime (2^60 - 93)
        elif bits == 40:
            primes.append(1099511627689) # A known 40-bit prime (2^40 - 87)
        elif bits == 30:
            primes.append(1073741789) # A known 30-bit prime (2^30 - 35)
        else:
            # Fallback for other bit sizes - this is not a prime
            primes.append((1 << bits) - 1)
    return primes

def _is_power_of_two(n: int) -> bool:
    return (n > 0) and (n & (n - 1) == 0)

class Context:
    """
    Manages global parameters for the CKKS HE scheme.
    """
    def __init__(
        self,
        poly_degree: int,
        ciphertext_moduli: List[int],
        scaling_factor: float = None,
        precision_bits: int = None,
        security_level: int = 128 # Conceptual
    ):
        """
        Initializes the CKKS context.

        Args:
            poly_degree (int): Degree of the polynomial ring (must be a power of 2).
            ciphertext_moduli (List[int]): List of prime moduli for the ciphertext space (q_i).
                                          Ordered from largest (level 0) to smallest.
            scaling_factor (float, optional): The initial scaling factor (delta).
                                              If None, calculated from precision_bits.
            precision_bits (int, optional): Desired bits of precision for fractional parts.
                                            Used if scaling_factor is None. Defaults to 20.
            security_level (int, optional): Conceptual cryptographic security strength.
        """
        if not _is_power_of_two(poly_degree):
            raise ValueError("Polynomial degree (poly_degree) must be a power of two.")
        if not ciphertext_moduli:
            raise ValueError("Ciphertext moduli list cannot be empty.")
        if not all(isinstance(q, int) and q > 0 for q in ciphertext_moduli):
            raise ValueError("All ciphertext moduli must be positive integers.")
        # In a real library, check if moduli are prime and suitable for NTT.

        self.poly_degree = poly_degree
        self.ciphertext_moduli = ciphertext_moduli # q_i, typically q_0 > q_1 > ...
        self.num_levels = len(ciphertext_moduli)

        if scaling_factor is None:
            if precision_bits is None:
                precision_bits = 20 # Default precision
            if not (isinstance(precision_bits, int) and precision_bits > 0):
                raise ValueError("precision_bits must be a positive integer.")
            self.scaling_factor = float(2**precision_bits)
            self.precision_bits = precision_bits
        else:
            if not (isinstance(scaling_factor, (float, int)) and scaling_factor > 0):
                raise ValueError("scaling_factor must be a positive number.")
            self.scaling_factor = float(scaling_factor)
            # Estimate precision_bits from scaling_factor if needed (optional)
            self.precision_bits = int(np.log2(scaling_factor)) if scaling_factor >= 1 else 0

        self.security_level = security_level # Conceptual for this library

        # Precompute roots of unity for X^N + 1, these are exp(i * pi * (2j+1) / N)
        # These are (2N)-th primitive roots of unity, specifically those whose square is an Nth root of -1.
        # For use in Encoder for FFT-like transforms.
        # The roots are exp(k * pi * 1j / poly_degree) for k = 1, 3, 5, ..., 2*poly_degree - 1
        # Or, more directly for X^N+1, roots are psi_j = exp( (2j+1) * pi * 1j / N ) for j = 0..N-1
        self.roots_of_unity = np.exp(
            (2 * np.arange(self.poly_degree) + 1) * np.pi * 1j / (2 * self.poly_degree)
        )
        # For encoding N/2 complex numbers, we typically use the first N/2 of these roots.

    def get_modulus_for_level(self, level: int) -> int:
        """
        Returns the ciphertext modulus q_i for a given computation level.
        Level 0 is the highest level (largest modulus).
        """
        if not (0 <= level < self.num_levels):
            raise ValueError(f"Invalid level: {level}. Must be between 0 and {self.num_levels - 1}.")
        # Convention: ciphertext_moduli = [q_max, ..., q_min]
        # Level 0 -> q_max (self.ciphertext_moduli[0])
        # Level (num_levels - 1) -> q_min (self.ciphertext_moduli[self.num_levels - 1])
        # So, if rescaling reduces level index, it means we go from q_i to q_{i+1}
        # Let's adjust level interpretation if needed.
        # The prompt's Python example: level decreases from max_levels down to 1 (or 0).
        # If level means "remaining levels", then max_level has modulus q_0.
        # If level means "current prime index", then level 0 uses q_0.
        # Let's assume level is an index into ciphertext_moduli.
        # Top level (max noise budget) = level 0, using self.ciphertext_moduli[0].
        # After one rescale, level becomes 1, using self.ciphertext_moduli[1].
        return self.ciphertext_moduli[level]

    @property
    def initial_scaling_factor(self) -> float:
        """Returns the initial scaling factor configured for the context."""
        return self.scaling_factor

    def __repr__(self) -> str:
        return (
            f"Context(poly_degree={self.poly_degree}, "
            f"num_levels={self.num_levels}, "
            f"initial_scaling_factor={self.initial_scaling_factor:.2f}, "
            f"top_modulus={self.ciphertext_moduli[0] if self.ciphertext_moduli else None})"
        )

if __name__ == '__main__':
    # Example Usage:
    # These primes are placeholders. Real applications need carefully chosen primes.
    # For poly_degree=8, N=8. Primes q_i should be 1 mod 16.
    # e.g. 17, 33 (not prime), 49 (not prime), 65 (not prime), 97
    # Let's use some example values that might not be cryptographically sound but work for structure.

    # Using placeholder primes that might not be NTT-friendly for small N for simplicity
    # For N=8, 2N=16. Primes must be q = 1 (mod 16) for NTT.
    # Example: 1152921504606846899 is not 1 mod 16. This highlights simplification.
    # For educational purposes, we might ignore NTT-friendliness for now,
    # as polynomial ops will use naive multiplication.

    example_moduli = _generate_primes_for_educational_purpose(2**4, [60,40])
    # For poly_degree = 2^4 = 16.
    # We need q_i = 1 (mod 32).
    # Let's manually pick some small ones if the generator is just a placeholder.
    # q0 = 97 (1 mod 32 is not true, 97 = 1 mod 32 is true, 97 = 3*32 + 1)
    # q1 = 65 (not prime)
    # q0 = 1152921504606846899 # 2^60-93. (2^60-93) % 32 = (..00 - 93) % 32 = (-93) % 32 = (-96+3)%32 = 3. Not NTT friendly.
    # This shows that the prime generation needs to be proper.
    # For now, we'll assume the user provides valid moduli or we use very specific examples.

    # Let's use a set of parameters that are more consistent for demonstration.
    # For poly_degree = N, moduli q should be primes with q = 1 (mod 2N).
    N_example = 2**4 # 16
    # Need q = 1 (mod 32)
    # Example: q0 = 97, q1 = 193, q2 = 257 (all are 1 mod 32, except 97 is 1 mod 32, 193 = 6*32+1, 257 = 8*32+1)
    # Let's use larger, more typical bit sizes for q_i

    # These are illustrative primes, not necessarily optimized for any N.
    # For the _generate_primes function to be useful, it needs a real prime finding algo.
    # We will assume the user provides a valid list of primes.

    custom_moduli = [1152921504606846899, 1099511627689] # Example 60-bit, 40-bit primes

    try:
        context = Context(
            poly_degree=2**12, # N = 4096
            ciphertext_moduli=custom_moduli,
            precision_bits=40 # delta = 2^40
        )
        print(context)
        print(f"Modulus at level 0: {context.get_modulus_for_level(0)}")
        print(f"Modulus at level 1: {context.get_modulus_for_level(1)}")
        # print(f"Roots of unity (first 3): {context.roots_of_unity[:3]}")

        context_from_scale = Context(
            poly_degree=2**4,
            ciphertext_moduli=[97, 61], # Small primes for example
            scaling_factor=1000.0
        )
        print(context_from_scale)
        print(f"Precision bits from scale: {context_from_scale.precision_bits}")


    except ValueError as e:
        print(f"Error: {e}")

```

Now, `plaintext.py`:
