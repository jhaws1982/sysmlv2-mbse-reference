/**
 * Shared — namespace hub for the 00_Shared layer.
 *
 * PURPOSE OF THIS FILE
 * ────────────────────
 * This is the ONE and ONLY declaration of  package Shared  in the entire model.
 * It assembles the leaf packages defined in this directory into a clean nested
 * namespace.  No other file declares  package Shared.
 *
 * HOW IT WORKS
 * ────────────
 * Leaf file  Data_Types.sysml  declares:
 *     package SharedData { ... }          ← globally unique flat name
 *
 * This hub file re-exports that leaf under the nested name:
 *     Shared::Data::*
 *
 * Consumers write:
 *     private import Shared::Data::*;     ← clean nested path, no shadowing
 *
 * The `public import` here is intentional and required: it makes SharedData's
 * members visible to anyone who imports Shared::Data.  Every other import in
 * the model is `private import`.
 */
package Shared {
    package Data {
        public import SharedData::*;
    }
}
