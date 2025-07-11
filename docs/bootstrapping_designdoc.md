# Micro Design Document: Bootstrapping (Conceptual Simulation)

## 1. Introduction

Bootstrapping is a transformative process in Fully Homomorphic Encryption (FHE) that "refreshes" a ciphertext. When a ciphertext has accumulated too much noise through many homomorphic operations, its underlying message can no longer be correctly decrypted. Bootstrapping takes such a noisy ciphertext, which is near its noise limit or has consumed all its computation levels, and produces a new ciphertext encrypting the same message but with reduced noise and reset to the highest modulus/level. This allows for virtually unlimited homomorphic computations.

In CKKS, bootstrapping is particularly complex, involving homomorphic evaluation of the decryption circuit, which includes encoding, DFT/FFT-like operations, and modular arithmetic. For this educational library, we will implement a **conceptual simulation** of bootstrapping, as described in the initial problem (ChatGPT conversation). This simulation will achieve the *effect* of bootstrapping (noise reset, level reset, scale reset) without implementing the full cryptographic machinery.

## 2. Purpose (Conceptual Simulation)

*   To provide a mechanism to reset the `noise_estimate`, `level`, and `scaling_factor` of a ciphertext to their initial states.
*   To simulate the ability to perform arbitrarily deep computations by "refreshing" ciphertexts.
*   To maintain the structure of the FHE library where a bootstrapping operation can be called, even if its internals are simplified for educational purposes.

## 3. The `Evaluator` Class Method (Conceptual Simulation)

*   **`bootstrap(self, ct: Ciphertext, secret_key_for_bootstrapping_simulation: SecretKey, public_key_for_bootstrapping_simulation: PublicKey, encoder_for_bootstrapping_simulation: Encoder) -> Ciphertext`**:
    *   Input:
        *   `ct: Ciphertext`: The noisy ciphertext to be bootstrapped.
        *   `secret_key_for_bootstrapping_simulation: SecretKey`: The secret key (normally this would be encrypted and used homomorphically, but here it's used directly for the simulation).
        *   `public_key_for_bootstrapping_simulation: PublicKey`: The public key to re-encrypt under.
        *   `encoder_for_bootstrapping_simulation: Encoder`: The encoder instance.
    *   Process (Simulated "Decrypt -> Encode -> Encrypt"):
        1.  **Simulated Decryption**:
            *   Internally use the provided `secret_key_for_bootstrapping_simulation` to decrypt `ct`. This would call a (potentially internal) decryption method.
            *   `decrypted_poly = self._decrypt_internal(ct, secret_key_for_bootstrapping_simulation)` (assuming `_decrypt_internal` returns the raw polynomial `m' = m + noise`).
            *   Create a temporary `Plaintext` object from `decrypted_poly`, `ct.scaling_factor`, and `ct.level`.
        2.  **Simulated Decoding**:
            *   Use the provided `encoder_for_bootstrapping_simulation` to decode this temporary `Plaintext` object back to approximate real/complex values.
            *   `decoded_values_approx = encoder_for_bootstrapping_simulation.decode(temp_plaintext_from_decryption)`
        3.  **Simulated Re-Encoding**:
            *   Re-encode these `decoded_values_approx` using the `encoder_for_bootstrapping_simulation`.
            *   The crucial part here is to use the `context.initial_scale` (the original, target scale after bootstrapping) and set the level to the maximum (top level).
            *   `new_plaintext = encoder_for_bootstrapping_simulation.encode(decoded_values_approx, self.context.initial_scale)`
            *   Set `new_plaintext.level = self.context.num_levels() - 1` (or the max level index).
        4.  **Simulated Re-Encryption**:
            *   Encrypt `new_plaintext` using the provided `public_key_for_bootstrapping_simulation`.
            *   `refreshed_ct = self._encrypt_internal(new_plaintext, public_key_for_bootstrapping_simulation)`
        5.  The `refreshed_ct` will inherently have:
            *   `level` set to the maximum.
            *   `scaling_factor` set to `context.initial_scale`.
            *   `noise_estimate` reset to the initial small value associated with fresh encryptions.
    *   Output: A new `Ciphertext` (`refreshed_ct`) that encrypts (approximately) the same message as `ct` but is "fresh".

## 4. "Real" Bootstrapping Sketch (Not Implemented, for Context)

A true CKKS bootstrapping procedure is vastly more complex:
1.  **Modulus Raising**: The input ciphertext `ct (mod q)` is transformed to `ct (mod Q >> q)`.
2.  **Slots to Coefficients**: Homomorphically transform the encrypted slot values (message) into coefficients of a polynomial representing the message. This involves evaluating an IFFT-like circuit.
3.  **Homomorphic Decryption Circuit Evaluation**:
    *   The decryption equation is `m = (c0 + c1*s) mod q`.
    *   The secret key `s` must be provided as an encrypted version: `Enc(s)`.
    *   The operations (polynomial multiplication by `Enc(s)`, addition, modular reduction by `q`) are performed homomorphically on `ct (mod Q)` and `Enc(s)`. This is the most challenging part.
4.  **Coefficients to Slots**: Homomorphically transform the resulting encrypted coefficients back into encrypted slot values (FFT-like circuit).
5.  **Modulus Reduction**: The ciphertext is reduced from `Q` back to a standard ciphertext modulus `q'`.

This process is computationally very expensive and requires careful parameter selection (e.g., `Q` must be large enough to evaluate the decryption circuit).

## 5. Implications of Simulation

*   **No Actual Homomorphic Evaluation**: The simulation does *not* perform the decryption circuit homomorphically. It uses the actual secret key. This means it's not a secure FHE bootstrapping in the cryptographic sense if the entity performing bootstrapping is not supposed to have the secret key.
*   **Educational Purpose**: The goal is to show the *role* and *effect* of bootstrapping in an FHE workflow (noise/level/scale reset).
*   **API Consistency**: Provides an `evaluator.bootstrap(...)` method that users can call, maintaining an API similar to full FHE libraries.
*   **Dependencies**: The simulated `bootstrap` method requires access to the `SecretKey`, `PublicKey`, and `Encoder` instances, which might not always be available to an `Evaluator` in a typical client-server FHE setup. This highlights the "simulation" aspect. The entity calling this simulated bootstrap must possess these components.

## 6. Ciphertext Attributes Affected

After bootstrapping (even simulated):
*   `ct.level`: Reset to the maximum level (e.g., `context.num_levels() - 1`).
*   `ct.scaling_factor`: Reset to `context.initial_scale`.
*   `ct.noise_estimate`: Reset to a small, initial value.
*   The ciphertext modulus is implicitly reset to the modulus of the highest level.

## 7. Example Usage (Simulated)

```python
# Assuming:
# context = Context(...)
# sk, pk, _, _ = keygen_function(context) # Generate keys
# encoder = Encoder(context)
# evaluator = Evaluator(context, public_key=pk, secret_key=sk, encoder=encoder) # Evaluator holds keys for simulation

# ct_noisy is a ciphertext that has undergone many operations
# ct_noisy.level might be low, ct_noisy.scaling_factor might be large, noise high.

# Perform simulated bootstrapping
# Note: In a real scenario, the evaluator on a server would not have 'sk'.
# This call implies the client (owner of sk) is doing this, or it's a pure simulation.
# For the conceptual simulation from the prompt:
# class CKKS:
#   def bootstrap(self, ciph): # self has access to decrypt, encrypt, initial_modulus, scale
#       plaintext_vector = self.decrypt(ciph) # uses self.secret_key, self.modulus, self.curr_scale
#       fresh_ct = self.encrypt(plaintext_vector) # uses self.public_key, self.initial_modulus, self.initial_scale
#       # ... reset self.curr_scale, self.modulus, self.cipher_noise for 'self' if ct is 'self'
#       return fresh_ct

# In our model:
# evaluator needs sk, pk, encoder for this simulation.
# Let's assume the main CKKS object or a test setup provides these to the bootstrap method.
# refreshed_ct = evaluator.bootstrap(ct_noisy, sk, pk, encoder)

# refreshed_ct now encrypts the same message (approximately) as ct_noisy,
# but has its level, scale, and noise reset.
```
The design of the `bootstrap` method in the prompt's final Python example (`CKKS` class) assumed the class instance itself held the necessary keys and parameters to perform this decrypt-encode-encrypt cycle. We will adapt this idea. The `Evaluator` or main `CKKS` class instance will need to be configured with (or have access to) the `SecretKey` and `PublicKey` if it's to perform this simulated bootstrapping.

This conceptual simulation provides a placeholder for one of FHE's most advanced features, making the library feel more complete for educational exploration of FHE workflows.
---
Next, `docs/ciphertext_designdoc.md`.
