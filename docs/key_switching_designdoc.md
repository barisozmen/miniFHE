# Micro Design Document: Key Switching

## 1. Introduction

Key switching is a fundamental cryptographic primitive in lattice-based FHE schemes like CKKS. It allows changing the secret key under which a ciphertext is encrypted without decrypting it. This is crucial for several advanced homomorphic operations:

1.  **Relinearization**: After multiplying two ciphertexts `ct_1(s)` and `ct_2(s)`, the result is a quadratic ciphertext `ct_quad(s, s^2)`. Key switching is used to transform the `s^2` part, effectively converting `ct_quad` back into a linear ciphertext `ct_lin(s)`. The "key" being switched from is `s^2` (or components of it) to `s`.
2.  **Rotations (Galois Automorphisms)**: Applying a Galois automorphism `ψ_k` to a ciphertext `ct(s(X))` results in `ct'(s(X^k))`. Key switching is then used to change the encryption from `s(X^k)` back to the original `s(X)`.

## 2. Purpose

*   To define a generic key-switching mechanism that can serve both relinearization and rotations.
*   To detail the structure of key-switching keys (which are specialized forms of `RelinKey` or `GaloisKey`).
*   To specify the algorithm for performing the key-switching operation.

## 3. Core Idea

Let `ct_old` be a ciphertext component that is effectively encrypted under a secret key `s_old`. We want to transform it into `ct_new_pair = (c0', c1')` such that `c0' + c1' * s_new` decrypts to (approximately) the same message that `ct_old` represented with `s_old`.

This is achieved using a **key-switching key**, `K_switch = (K_0, K_1)`, which is an encryption of `s_old` under `s_new`:
`K_0 + K_1 * s_new \approx P * s_old` (modulo `q`)
Here, `P` is a special modulus (or a power of a base `w` used for digit decomposition) that is part of the key generation process. It's used to improve noise performance. `q` is the ciphertext modulus.

The key-switching operation then computes:
`c0' = round(ct_old * K_0 / P) mod q`
`c1' = round(ct_old * K_1 / P) mod q`

The resulting `(c0', c1')` is a 2-component ciphertext that is now effectively linear in `s_new`.

## 4. Key-Switching Key (`KeySwitchKey`)

A `KeySwitchKey` object will store the necessary components. In practice, to manage noise, `ct_old` is often decomposed into digits (base `w` or `P`), and the key `K_switch` consists of multiple such pairs `(K_0_i, K_1_i)`, one for each digit/power of the decomposition base.

*   **Attributes of a `KeySwitchKey` (for a single `s_old` to `s_new` transformation):**
    *   `key_components`: `list[tuple[Polynomial, Polynomial]]`
        *   Each tuple `(K_0_j, K_1_j)` is a pair of polynomials.
        *   `K_0_j + K_1_j * s_new \approx P * w^j * s_old` (if `w` is the decomposition base).
    *   `source_key_id`: Identifier for `s_old` (e.g., hash of `s_old`, or an ID like "s_squared" or "s_X_pow_k").
    *   `target_key_id`: Identifier for `s_new` (e.g., hash of `s_new`, typically the main secret key `s`).
    *   `decomposition_base` (P or w): `int`. The base used for decomposing the input polynomial.
    *   `num_digits`: `int`. Number of digits the input polynomial will be decomposed into.

*   **Generation (`KeyGenerator` method):**
    *   `generate_key_switch_key(s_old_poly, s_new_poly, decomp_base, num_digits, current_q, key_modulus_p)`:
        1.  For each digit `j` from `0` to `num_digits-1`:
            *   `term_to_encrypt = (key_modulus_p * (decomp_base^j) * s_old_poly) mod current_q`
            *   Sample `a_j` uniformly from R_q.
            *   Sample error `e_j` from error distribution.
            *   `b_j = (-a_j * s_new_poly + e_j + term_to_encrypt) mod current_q`.
            *   Store `(b_j, a_j)` as `(K_0_j, K_1_j)`.
    *   This `key_modulus_p` (the `P` in `P * s_old`) is crucial. It's often one of the large primes from the modulus chain (e.g., the largest available, or a dedicated prime).

## 5. The `Evaluator` Method for Key Switching

This will be a core internal method used by `relinearize` and `rotate`.

*   **`_key_switch_internal(self, poly_to_switch: Polynomial, ks_key: KeySwitchKey, current_q: int) -> (Polynomial, Polynomial)`**:
    *   Input:
        *   `poly_to_switch`: The polynomial whose encryption needs its key changed (e.g., `d2` from multiplication, or `c1(X^k)` from rotation).
        *   `ks_key`: The `KeySwitchKey` object.
        *   `current_q`: The current ciphertext modulus.
    *   Process:
        1.  **Decomposition (Base `w` decomposition)**:
            *   Decompose `poly_to_switch` into `d` digits/coefficients `coeff_j` such that `poly_to_switch = sum_{j=0}^{d-1} coeff_j * w^j`. (This is a coefficient-wise decomposition if `poly_to_switch` is an R_q element).
            *   The `coeff_j` are polynomials with small coefficients (e.g., in `[-w/2, w/2]`).
            *   The `ks_key.decomposition_base` is `w`.
            *   The `ks_key.key_components` are `[(K_0_0, K_1_0), (K_0_1, K_1_1), ..., (K_0_{d-1}, K_1_{d-1})]`.
        2.  **Main Computation**:
            *   Initialize `res_c0 = 0`, `res_c1 = 0` (polynomials).
            *   For `j` from `0` to `d-1` (number of digits/key components):
                *   Let `(K_0_j, K_1_j)` be `ks_key.key_components[j]`.
                *   `decomposed_part_j = extract_digit(poly_to_switch, j, ks_key.decomposition_base)` (This extracts the j-th digit/coefficient polynomial).
                *   `term0_j = (decomposed_part_j * K_0_j) mod current_q`
                *   `term1_j = (decomposed_part_j * K_1_j) mod current_q`
                *   `res_c0 = (res_c0 + term0_j) mod current_q`
                *   `res_c1 = (res_c1 + term1_j) mod current_q`
        3.  **Final Division by `P` (or `key_modulus_p`)**:
            *   The key generation for `K_0_j, K_1_j` included `P * ...`. So, `res_c0` and `res_c1` implicitly have this `P`.
            *   `final_c0 = round_and_divide_by_p(res_c0, ks_key.key_modulus_p) mod current_q`
            *   `final_c1 = round_and_divide_by_p(res_c1, ks_key.key_modulus_p) mod current_q`
            *   `round_and_divide_by_p(poly, p_mod)` would be `np.round(poly_coeffs / p_mod)`.
            *   This "division by P" is crucial for correctness and noise management. `P` is the `key_modulus_p` used when generating the key switch key.
    *   Output: `(final_c0, final_c1)`, a pair of polynomials.

## 6. Application in Relinearization

*   Input: `ct_quad = (d0, d1, d2)`, where `d2` is the coefficient of `s^2`.
*   `s_old` is effectively `s^2`. `s_new` is `s`.
*   `relin_key` is a `KeySwitchKey` generated for `s_old = s^2`, `s_new = s`.
*   `(switched_d2_c0, switched_d2_c1) = _key_switch_internal(d2, relin_key, current_q)`.
*   New ciphertext: `ct_new = ( (d0 + switched_d2_c0) mod q, (d1 + switched_d2_c1) mod q )`.

## 7. Application in Rotations

*   Input: `ct_aut = (c0_aut, c1_aut)`, where `c0_aut = c0(X^k)`, `c1_aut = c1(X^k)`. This is encrypted under `s_old = s(X^k)`.
*   `s_new` is `s(X)`.
*   `galois_key_for_k` is a `KeySwitchKey` generated for `s_old = s(X^k)`, `s_new = s(X)`.
*   `(switched_c1_aut_c0, switched_c1_aut_c1) = _key_switch_internal(c1_aut, galois_key_for_k, current_q)`.
*   New ciphertext: `ct_new = ( (c0_aut + switched_c1_aut_c0) mod q, switched_c1_aut_c1 mod q )`.

## 8. Digit Decomposition (`extract_digit`, `decomposition_base`)

*   The `decomposition_base` `w` (often called gadget base) and `num_digits` are parameters of the key switching key.
*   `poly_to_switch` is decomposed into coefficient vectors `d_i(X)` such that `poly_to_switch(X) = sum_i d_i(X) w^i`.
*   The `d_i(X)` have small norm coefficients.
*   The `KeySwitchKey` then has components for each `w^i * s_old`.
*   For simplicity in an educational library, we might initially skip digit decomposition or use a very simple form (e.g., `w` is large, so only one digit, `d_0 = poly_to_switch`). This would mean `ks_key.key_components` has only one element, and `P` is the `key_modulus_p`. This matches the "Simpler Conceptual Relinearization" from `operations_designdoc.md`.

**Simplified Key Switching (No explicit digit decomposition, `P` is `key_modulus_p` from keygen):**
Assume `ks_key.key_components` is just one pair `(K_0, K_1)`.
`K_0 + K_1 * s_new \approx P * s_old`.
`res_c0 = (poly_to_switch * K_0) mod current_q`
`res_c1 = (poly_to_switch * K_1) mod current_q`
`final_c0 = np.round(res_c0_coeffs / P) % current_q` (coefficient-wise)
`final_c1 = np.round(res_c1_coeffs / P) % current_q` (coefficient-wise)

This simplified version will be adopted for the educational library to maintain clarity. The `P` factor (named `key_modulus_p` during key generation and stored in the key) is essential.

## 9. Noise Implications

Key switching is a primary source of noise in FHE. The quality of the key (size of `P` or `w`, number of digits, noise in `K_i` components) directly impacts the noise added. The parameters must be chosen carefully.

This detailed design for key switching provides a robust foundation for implementing relinearization and rotations, which are key to the versatility of the CKKS scheme.
---
Next, `docs/bootstrapping_designdoc.md`.
