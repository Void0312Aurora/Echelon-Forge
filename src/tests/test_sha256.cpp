#include "runtime/crypto/sha256.h"

#include <doctest/doctest.h>

#include <string>

TEST_SUITE("sha256") {
    TEST_CASE("shared primitive matches standard vectors") {
        CHECK(runtime::crypto::sha256_hex("") ==
              "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855");
        CHECK(runtime::crypto::sha256_hex("abc") ==
              "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
        CHECK(runtime::crypto::sha256_hex("The quick brown fox jumps over the lazy dog") ==
              "d7a8fbb307d7809469ca9abcb0082e4f8d5651e46d3cdb762d02d0bf37c9e592");
    }

    TEST_CASE("shared primitive handles binary and block boundaries") {
        std::string binary(256, '\0');
        for (std::size_t index = 0; index < binary.size(); ++index) {
            binary[index] = static_cast<char>(index);
        }
        CHECK(runtime::crypto::sha256_hex(binary) ==
              "40aff2e9d2d8922e47afd4648e6967497158785fbd1da870e7110266bf944880");

        std::string block_boundary(55, 'a');
        CHECK(runtime::crypto::sha256_hex(block_boundary) ==
              "9f4390f8d30c2dd92ec9f095b65e2b9ae9b0a925a5258e241c9f1e910f734318");
        block_boundary.push_back('a');
        CHECK(runtime::crypto::sha256_hex(block_boundary) ==
              "b35439a4ac6f0948b6d6f9e3c6af0f5f590ce20f1bde7090ef7970686ec6738a");
    }
}
