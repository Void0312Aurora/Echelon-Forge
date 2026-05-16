#include "simulation_kernel.h"

#include "core/interfaces/environment_model.h"
#include "systems/visual/visual_system.h"

#include <cstddef>
#include <stdexcept>
#include <vector>

namespace {
bool collect_visual_scene(
    SimulationKernel& kernel,
    uint64_t entity_id,
    Math::Vector3& cam_pos,
    double& cam_heading,
    double& cam_pitch,
    std::vector<arb::VisibleObject>& objects,
    int& my_side
) {
    auto e = kernel.get_world().entity(entity_id);
    if (!e.is_valid()) {
        return false;
    }

    const Transform* cam_t = e.get<Transform>();
    const Alliance* cam_a = e.get<Alliance>();
    if (!cam_t) {
        return false;
    }

    cam_pos = {cam_t->x, cam_t->y, cam_t->z};
    cam_heading = cam_t->heading;
    cam_pitch = cam_t->pitch;
    my_side = cam_a ? static_cast<int>(cam_a->side) : 0;

    objects.clear();
    kernel.get_world().each([&](flecs::entity other_e, const Transform& t, const Velocity& v, const Alliance& a, const KeyEntity& k) {
        if (other_e.id() == entity_id) {
            return;
        }

        arb::VisibleObject obj;
        obj.x = t.x;
        obj.y = t.y;
        obj.z = t.z;
        obj.vx = v.vx;
        obj.vy = v.vy;
        obj.vz = v.vz;

        switch (k.type) {
            case UnitType::Aircraft: obj.bounding_radius = 10.0; obj.cls = 0; break;
            case UnitType::Ship: obj.bounding_radius = 50.0; obj.cls = 2; break;
            case UnitType::Submarine: obj.bounding_radius = 40.0; obj.cls = 2; break;
            case UnitType::Missile: obj.bounding_radius = 2.0; obj.cls = 0; break;
            case UnitType::Facility: obj.bounding_radius = 20.0; obj.cls = 1; break;
            default: obj.bounding_radius = 5.0; obj.cls = 1; break;
        }

        const int other_side = static_cast<int>(a.side);
        if (other_side == my_side) {
            obj.team = 1;
        } else if (other_side == 0) {
            obj.team = 0;
        } else {
            obj.team = -1;
        }

        objects.push_back(obj);
    });

    return true;
}
} // namespace

std::vector<float> SimulationKernel::get_visual_observation(uint64_t entity_id) {
    using namespace arb;

    std::vector<float> output(ARB_HEIGHT * ARB_WIDTH * ARB_CHANNELS, 0.0f);
    Math::Vector3 cam_pos{};
    double cam_heading = 0.0;
    double cam_pitch = 0.0;
    int my_side = 0;
    std::vector<VisibleObject> objects;
    if (!collect_visual_scene(*this, entity_id, cam_pos, cam_heading, cam_pitch, objects, my_side)) {
        return output;
    }

    RetinaBuffer buf;
    render_retina(cam_pos, cam_heading, cam_pitch, 180.0, 90.0, objects, environment_model_.get(), buf);
    buf.to_tensor(output.data());

    return output;
}

std::vector<float> SimulationKernel::get_visual_observation_downsampled(uint64_t entity_id, int factor) {
    using namespace arb;

    const int downsample = factor > 1 ? factor : 1;
    if (ARB_HEIGHT % downsample != 0 || ARB_WIDTH % downsample != 0) {
        throw std::invalid_argument("visual downsample factor must divide native ARB dimensions");
    }

    Math::Vector3 cam_pos{};
    double cam_heading = 0.0;
    double cam_pitch = 0.0;
    int my_side = 0;
    std::vector<VisibleObject> objects;
    if (!collect_visual_scene(*this, entity_id, cam_pos, cam_heading, cam_pitch, objects, my_side)) {
        return std::vector<float>(
            static_cast<size_t>(ARB_HEIGHT / downsample) * static_cast<size_t>(ARB_WIDTH / downsample) * static_cast<size_t>(ARB_CHANNELS),
            0.0f
        );
    }

    return render_retina_tensor(
        cam_pos,
        cam_heading,
        cam_pitch,
        180.0,
        90.0,
        objects,
        environment_model_.get(),
        ARB_HEIGHT / downsample,
        ARB_WIDTH / downsample
    );
}
