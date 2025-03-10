from orgsim import framework, models


def dummy_world_seed() -> framework.WorldSeed:
    return framework.WorldSeed(
        initial_people=[],
        fiscal_length=1,
        productivity=1,
        initial_personal_gain=0,
        selfish_gain=0,
        selfless_gain=0,
        living_cost=0,
        periodic_recruit_count=0,
        max_age=0,
    )


def dummy_person_seed(identity: str = "test") -> framework.PersonState:
    return framework.PersonSeed(identity=identity, selfishness=0.0)


def test_all_equal() -> None:
    seed = dummy_world_seed()
    state = framework.WorldState(
        seed=seed,
        date=0,
        people_states={
            "foo": framework.PersonState(seed=dummy_person_seed(identity="foo")),
            "bar": framework.PersonState(seed=dummy_person_seed(identity="bar")),
            "baz": framework.PersonState(seed=dummy_person_seed(identity="baz")),
        },
        total_reward=3,
        fiscal_period=0,
    )
    strat = models.AllEqual()
    strat.distribute_rewards(state=state)

    assert state.people_states["foo"].gain == 1.0
    assert state.people_states["bar"].gain == 1.0
    assert state.people_states["baz"].gain == 1.0


def test_equal_contribution() -> None:
    seed = dummy_world_seed()
    state = framework.WorldState(
        seed=seed,
        date=0,
        people_states={
            "foo": framework.PersonState(
                seed=dummy_person_seed(identity="foo"), contributions=0
            ),
            "bar": framework.PersonState(
                seed=dummy_person_seed(identity="bar"), contributions=1
            ),
            "baz": framework.PersonState(
                seed=dummy_person_seed(identity="baz"), contributions=2
            ),
        },
        total_reward=3,
        fiscal_period=0,
    )
    strat = models.EqualContribution()
    strat.distribute_rewards(state=state)

    assert state.people_states["foo"].gain == 0.0
    assert state.people_states["bar"].gain == 1.0
    assert state.people_states["baz"].gain == 2.0
