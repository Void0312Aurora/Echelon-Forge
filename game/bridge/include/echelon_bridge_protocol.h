#pragma once

#include <cstdint>
#include <string>

namespace epx {

struct BackendConfig {
    std::string host = "127.0.0.1";
    std::uint16_t port = 8765;
    std::string session_id = "arma_local";
};

struct ProxyStateCache {
    std::string sqf_payload =
        "[0,[0,0,100],[0,0,0],[1,0,0],[0,0,1],0,0,0,0]";
    std::string last_host_frame_sqf;
    std::string last_backend_line;
    std::string last_error;
    std::string last_context;
    std::uint64_t frame_counter = 0;
    bool session_active = false;
};

}  // namespace epx
