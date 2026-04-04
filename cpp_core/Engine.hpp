#pragma once

#include <iostream>
#include <vector>
#include <string>
#include <map>
#include <chrono>
#include <mutex>
#include <thread>
#include <atomic>
#include <memory>

namespace SatTrade {

// ─── DATA MODELS ─────────────────────────────────────────────────────────────

enum class AssetType { EQUITY, OPTION, COMMODITY, CRYPTO };
enum class OrderSide { BUY, SELL };
enum class OptionType { CALL, PUT };

struct MarketQuote {
    std::string ticker;
    double bid;
    double ask;
    long long volume;
    double last_price;
    std::chrono::system_clock::time_point timestamp;
};

struct Order {
    std::string order_id;
    std::string ticker;
    OrderSide side;
    AssetType asset_type;
    double quantity;
    double limit_price;
    OptionType option_type; // Only if asset_type == OPTION
    double strike_price;   // Only if asset_type == OPTION
    bool is_filled = false;
};

// ─── SIGNAL FUSION CORE ───────────────────────────────────────────────────────

class AlphaEngine {
public:
    AlphaEngine() : gtfi_score(1.0), is_running(false) {}

    void start() {
        is_running = true;
        fusion_thread = std::thread(&AlphaEngine::fusion_loop, this);
    }

    void stop() {
        is_running = false;
        if (fusion_thread.joinable()) fusion_thread.join();
    }

    void update_signal(const std::string& source, double impact) {
        std::lock_guard<std::mutex> lock(signal_mutex);
        signals[source] = impact;
        recalculate_gtfi();
    }

    double get_gtfi() const { return gtfi_score.load(); }

private:
    void fusion_loop() {
        while (is_running) {
            // High-frequency signal synthesis
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
    }

    void recalculate_gtfi() {
        double aggregate = 1.0;
        for (const auto& [source, impact] : signals) {
            aggregate -= impact;
        }
        gtfi_score.store(std::max(0.0, std::min(1.0, aggregate)));
    }

    std::map<std::string, double> signals;
    std::mutex signal_mutex;
    std::atomic<double> gtfi_score;
    std::atomic<bool> is_running;
    std::thread fusion_thread;
};

// ─── ORDER MANAGEMENT SYSTEM ────────────────────────────────────────────────

class OMS {
public:
    void place_order(const Order& order) {
        std::lock_guard<std::mutex> lock(order_mutex);
        orders.push_back(order);
        std::cout << "[OMS] Order Placed: " << order.ticker 
                  << (order.side == OrderSide::BUY ? " BUY " : " SELL ")
                  << order.quantity << " @ " << order.limit_price;
        
        if (order.asset_type == AssetType::OPTION) {
            std::cout << " (" << (order.option_type == OptionType::CALL ? "CALL" : "PUT") 
                      << " STRIKE: " << order.strike_price << ")";
        }
        std::cout << std::endl;
    }

    void execute_market_match(const std::string& ticker, double price) {
        std::lock_guard<std::mutex> lock(order_mutex);
        for (auto& o : orders) {
            if (!o.is_filled && o.ticker == ticker) {
                if ((o.side == OrderSide::BUY && price <= o.limit_price) ||
                    (o.side == OrderSide::SELL && price >= o.limit_price)) {
                    o.is_filled = true;
                    std::cout << "[OMS] ORDER FILLED: " << o.order_id << " " << ticker << " @ " << price << std::endl;
                }
            }
        }
    }

private:
    std::vector<Order> orders;
    std::mutex order_mutex;
};

} // namespace SatTrade
