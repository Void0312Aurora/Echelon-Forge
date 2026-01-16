#include "core/effects_model.h"

#include <spdlog/spdlog.h>

#include "components/health.h"
#include "components/scoring.h"

namespace {

class DefaultEffectsModel : public IEffectsModel {
public:
    EffectsResult on_proximity_hit(flecs::world world,
                                   flecs::entity missile_entity,
                                   const Missile& missile,
                                   flecs::entity target_entity) override {
        EffectsResult result;

        bool destroyed = false;
        Score* score = nullptr;
        auto attacker = world.entity(missile.attacker_id);
        if (attacker.is_valid()) {
            score = attacker.get_mut<Score>();
        }

        Health* hp = target_entity.get_mut<Health>();
        if (hp) {
            hp->current_hp -= missile.damage;

            if (score) {
                score->total_reward += missile.damage;
                score->hits_landed++;
            }

            spdlog::info("HIT! Missile {} hit Target {} for {:.1f} dmg. Rem HP: {:.1f}",
                         missile_entity.id(), target_entity.id(), missile.damage, hp->current_hp);

            if (hp->current_hp <= 0) {
                target_entity.destruct();
                destroyed = true;
                spdlog::info("SPLASH! Target {} Destroyed.", target_entity.id());
            }
        } else {
            target_entity.destruct();
            destroyed = true;
            spdlog::info("SPLASH! Target {} Destroyed (No HP).", target_entity.id());
        }

        if (destroyed && score) {
            score->total_reward += 1000.0;
            score->kills_confirmed++;
        }

        return result;
    }
};

} // namespace

std::unique_ptr<IEffectsModel> make_default_effects_model() {
    return std::make_unique<DefaultEffectsModel>();
}
