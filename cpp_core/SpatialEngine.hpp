#pragma once

#include <vector>
#include <cmath>
#include <algorithm>
#include <map>
#include <string>

namespace SatTrade {

struct Point {
    double lat;
    double lon;
    double value;
    std::string id;
};

struct Cluster {
    double center_lat;
    double center_lon;
    double total_value;
    int point_count;
    std::vector<std::string> point_ids;
};

class SpatialEngine {
public:
    /**
     * Fast grid-based clustering. O(N) complexity.
     * Perfect for grouping thousands of thermal hotspots into industrial clusters.
     */
    static std::vector<Cluster> cluster_points(const std::vector<Point>& points, double grid_km) {
        double grid_deg = grid_km / 111.32; // Simplified degree conversion
        std::map<std::pair<int, int>, Cluster> grid;

        for (const auto& p : points) {
            int lat_idx = static_cast<int>(std::floor(p.lat / grid_deg));
            int lon_idx = static_cast<int>(std::floor(p.lon / grid_deg));
            auto key = std::make_pair(lat_idx, lon_idx);

            auto& cluster = grid[key];
            if (cluster.point_count == 0) {
                cluster.center_lat = p.lat;
                cluster.center_lon = p.lon;
            } else {
                // Moving average for center
                cluster.center_lat = (cluster.center_lat * cluster.point_count + p.lat) / (cluster.point_count + 1);
                cluster.center_lon = (cluster.center_lon * cluster.point_count + p.lon) / (cluster.point_count + 1);
            }
            cluster.total_value += p.value;
            cluster.point_count++;
            cluster.point_ids.push_back(p.id);
        }

        std::vector<Cluster> result;
        for (auto const& [key, cluster] : grid) {
            result.push_back(cluster);
        }
        return result;
    }

    /**
     * High-speed Haversine distance calculation.
     */
    static double haversine(double lat1, double lon1, double lat2, double lon2) {
        double dLat = (lat2 - lat1) * M_PI / 180.0;
        double dLon = (lon2 - lon1) * M_PI / 180.0;

        lat1 = lat1 * M_PI / 180.0;
        lat2 = lat2 * M_PI / 180.0;

        double a = std::pow(std::sin(dLat / 2), 2) +
                   std::pow(std::sin(dLon / 2), 2) * std::cos(lat1) * std::cos(lat2);
        double rad = 6371.0;
        double c = 2 * std::asin(std::sqrt(a));
        return rad * c;
    }
};

} // namespace SatTrade
