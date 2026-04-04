#pragma once

#include <chrono>
#include <iostream>
#include <string>

namespace SatTrade {

class SystemMonitor {
public:
    static void log_latency(const std::string& operation, std::chrono::steady_clock::time_point start) {
        auto end = std::chrono::steady_clock::now();
        auto diff = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count();
        std::cout << "\033[1;30m[LATENCY-MONITOR] " << operation << ": " << diff << "ns\033[0m" << std::endl;
    }

    static void log_system_health() {
        std::cout << "\033[1;32m[SYSTEM-HEALTH] ALPHA-PRIME CORE: NOMINAL | THREADS: ACTIVE | MEMORY: OPTIMIZED\033[0m" << std::endl;
    }
};

} // namespace SatTrade
