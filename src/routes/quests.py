from datetime import datetime

from sanic import Blueprint, Request
import sanic
from sanic_ext import openapi, validate
from sanic_ext.extensions.openapi.definitions import Parameter, RequestBody, Response

from src.utils.errors import BadRequest400, NotFound404

from src.database import Database

from src.models.quests import objective, quest, quest_progress, reward

# Specific for Migration
from src.models.quests.objective_customization.customization import Customizations, LocationCustomization, MainhandCustomization, \
    MaximumDeathsCustomization, NaturalBlockCustomization, TimerCustomization
from src.models.quests.objective_targets.target import KillTargetModel, MineTargetModel, EncounterTargetModel

quest_blueprint = Blueprint("quests", url_prefix='/quests')


@quest_blueprint.route('/', methods=['POST'])
@openapi.definition(body=RequestBody(quest.QuestCreateModel.doc_schema()),
                    response=[
                        Response(quest.QuestModel.doc_schema(), 201),
                        Response(BadRequest400, 400)
                    ])
@validate(json=quest.QuestCreateModel)
async def create_quest(request: Request, db: Database, body: quest.QuestCreateModel):
    """
    Create New Quest

    Creates a new quest based on the information provided.
    Some fields are optional and can be `null` while others are required.
    Check the schema for more info on that.
    """
    quest_id = await quest.QuestModel.create(db, body)
    quest_model = await quest.QuestModel.fetch(db, quest_id)

    return sanic.json(status=201, body=quest_model.model_dump(), default=str)


@quest_blueprint.route('/', methods=['GET'])
@openapi.definition(response=[
    Response(quest.QuestListModel.doc_schema(), 200),
],
    parameter=[
        Parameter('creator_thorny_ids', list[int], description="Filter by creator"),
        Parameter('quest_types', list[str], description="Filter by quest type"),
        Parameter('time_start', datetime, description="The start time to filter by"),
        Parameter('time_end', datetime, description="The end time to filter by"),
        Parameter('active', bool, description="Filter by active quests"),
        Parameter('future', bool, description="Filter by future quests"),
        Parameter('past', bool, description="Filter by past quests"),
        Parameter('page', int, description="The page to return. Default: 1"),
        Parameter('page_size', int, description="The size of each page in items. Default: 100")
    ])
async def get_all_quests(request: Request, db: Database):
    """
    Get All Quests

    Returns all quests ordered by start date, recent first
    """
    creator_thorny_ids = request.args.getlist('creator_thorny_ids')
    quest_types = request.args.getlist('quest_types')
    time_start = request.args.get('time_start')
    time_end = request.args.get('time_end')
    active = request.args.get('active')
    future = request.args.get('future')
    past = request.args.get('past')

    page = request.args.get('page')
    page_size = request.args.get('page_size')

    quests_model = await quest.QuestListModel.fetch(db,
                                                    time_start,
                                                    time_end,
                                                    creator_thorny_ids,
                                                    quest_types,
                                                    active,
                                                    future,
                                                    past)

    return sanic.json(quests_model.model_dump(), default=str)


@quest_blueprint.route('/<quest_id:int>', methods=['GET'])
@openapi.definition(response=[
                        Response(quest.QuestModel.doc_schema(), 200),
                        Response(NotFound404, 404)
                    ])
async def get_quest(request: Request, db: Database, quest_id: int):
    """
    Get Quest

    Returns a specific quest, objectives and rewards
    """
    quest_model = await quest.QuestModel.fetch(db, quest_id)

    return sanic.json(quest_model.model_dump(), default=str)


@quest_blueprint.route('/<quest_id:int>/objectives', methods=['GET'])
@openapi.definition(response=[
                        Response(objective.ObjectivesListModel.doc_schema(), 200)
                    ])
async def get_objectives(request: Request, db: Database, quest_id: int):
    """
    Get All Objectives

    Returns a list of all the objectives a quest has
    """
    objectives_model = await objective.ObjectivesListModel.fetch(db, quest_id)

    return sanic.json(objectives_model.model_dump(), default=str)


@quest_blueprint.route('/<quest_id:int>/objectives/<objective_id:int>', methods=['GET'])
@openapi.definition(response=[
                        Response(objective.ObjectiveModel.doc_schema(), 200),
                        Response(NotFound404, 404)
                    ])
async def get_objective(request: Request, db: Database, quest_id: int, objective_id: int):
    """
    Get Objective

    Returns the specified objective
    """
    objective_model = await objective.ObjectiveModel.fetch(db, quest_id, objective_id)

    return sanic.json(objective_model.model_dump(), default=str)


@quest_blueprint.route('/<quest_id:int>/objectives/<objective_id:int>/rewards', methods=['GET'])
@openapi.definition(response=[
                        Response(reward.RewardsListModel.doc_schema(), 200)
                    ])
async def get_rewards(request: Request, db: Database, quest_id: int, objective_id: int):
    """
    Get All Rewards

    Returns all the rewards of the specified objective
    """
    rewards_model = await reward.RewardsListModel.fetch(db, quest_id, objective_id)

    return sanic.json(rewards_model.model_dump(), default=str)


@quest_blueprint.route('/<quest_id:int>', methods=['PATCH', 'PUT'])
@openapi.definition(body=RequestBody(quest.QuestUpdateModel.doc_schema()),
                    response=[
                        Response(quest.QuestModel.doc_schema(), 200),
                        Response(BadRequest400, 400),
                        Response(NotFound404, 404)
                    ])
@validate(json=quest.QuestUpdateModel)
async def update_quest(request: Request, db: Database, quest_id: int, body: quest.QuestUpdateModel):
    """
    Update Quest

    Update a quest
    """
    model = await quest.QuestModel.fetch(db, quest_id)
    await model.update(db, body)

    return sanic.json(model.model_dump(), default=str)


@quest_blueprint.route('/reward/<reward_id:int>', methods=['PATCH', 'PUT'])
@openapi.definition(body=RequestBody(reward.RewardUpdateModel.doc_schema()),
                    response=[
                        Response(reward.RewardModel.doc_schema(), 200),
                        Response(BadRequest400, 400),
                        Response(NotFound404, 404)
                    ])
@validate(json=reward.RewardUpdateModel)
async def update_reward(request: Request, db: Database, reward_id: int, body: reward.RewardUpdateModel):
    """
    Update Reward

    Update an objective's reward
    """
    model = await reward.RewardModel.fetch(db, reward_id)
    await model.update(db, body)

    return sanic.json(model.model_dump(), default=str)


@quest_blueprint.route('/objective/<objective_id:int>', methods=['PATCH', 'PUT'])
@openapi.definition(body=RequestBody(objective.ObjectiveUpdateModel.doc_schema()),
                    response=[
                        Response(objective.ObjectiveModel.doc_schema(), 200),
                        Response(BadRequest400, 400),
                        Response(NotFound404, 404)
                    ])
@validate(json=objective.ObjectiveUpdateModel)
async def update_objective(request: Request, db: Database, objective_id: int, body: objective.ObjectiveUpdateModel):
    """
    Update Objective

    Update a quest's objective
    """
    model = await objective.ObjectiveModel.fetch(db, objective_id)
    await model.update(db, body)

    return sanic.json(model.model_dump(), default=str)


@quest_blueprint.route('/migrate_data', methods=['PUT'])
@openapi.definition(response=[
                        Response(quest.QuestListModel.doc_schema(), 200),
                        Response(BadRequest400, 400),
                        Response(NotFound404, 404)
                    ])
async def migrate(request: Request, db: Database):
    """
    Migrate Quest Data

    From the old V2 quests to V3. This also combines the old V1 quest data for full consistency.
    """
    # Fetches quests which were ported to V2, but fetches the V1 data to port over to V3
    v1_quests = await db.pool.fetch("""
                                    select uq.*,
                                        oq.title,
                                        oq.description,
                                        q.start_time,
                                        q.end_time,
                                        oq.objective,
                                        oq.objective_count,
                                        oq.objective_type,
                                        oq.required_mainhand,
                                        oq.required_location,
                                        oq.location_radius,
                                        oq.required_timer,
                                        oq.balance_reward,
                                        oq.item_reward,
                                        oq.item_reward_count from users.quests uq
                                    inner join quests.quest q on uq.quest_id = q.quest_id
                                    inner join quests oq on oq.title = q.title and oq.start_time = q.start_time;
                                    """)

    # {quest_id: {"v3_id": 43}}
    v1_quest_memory: dict[int, dict] = {}

    for q_v1 in v1_quests:
        # Quest doesn't exist in the DB. Create it
        if v1_quest_memory.get(q_v1["quest_id"], None) is None:
            if q_v1["objective_type"] == 'kill':
                target = KillTargetModel(target_type='kill', entity=q_v1["objective"], count=q_v1["objective_count"])
            else:
                target = MineTargetModel(target_type='mine', block=q_v1["objective"], count=q_v1["objective_count"])

            customizations = Customizations()

            if q_v1["required_mainhand"]:
                customizations.mainhand = MainhandCustomization(item=q_v1["required_mainhand"])
            if q_v1["required_location"]:
                customizations.location = LocationCustomization(
                    coordinates=(q_v1["required_location"][0], 70, q_v1["required_location"][1]),
                    horizontal_radius=q_v1["location_radius"],
                    vertical_radius=q_v1["location_radius"],
                )

            create_model = quest.QuestCreateModel(
                start_time=q_v1["start_time"],
                end_time=q_v1["end_time"],
                title=q_v1["title"],
                description=q_v1["description"],
                created_by=15,
                tags=['v1 Quest'],
                quest_type='minor',
                objectives=[
                    objective.ObjectiveCreateModel(
                        description=q_v1["description"],
                        objective_type=q_v1["objective_type"],
                        display=None,
                        order_index=0,
                        logic="and",
                        target_count=None,
                        targets=[target],
                        customizations=customizations,
                        rewards=[reward.RewardCreateModel(balance=q_v1["balance_reward"], item=q_v1["item_reward"], count=q_v1["item_reward_count"], display_name=None, item_metadata=[])],
                    )
                ]
            )

            quest_id = await quest.QuestModel.create(db, create_model)
            v1_quest_memory[q_v1["quest_id"]] = {"v3_id": quest_id}

        v3_id = v1_quest_memory[q_v1.quest_id]["v3_id"]
        progress_id = await quest_progress.QuestProgressModel.create(db, quest_progress.QuestProgressCreateModel(quest_id=v3_id, thorny_id=q_v1.thorny_id))

        await db.pool.execute("""
                              UPDATE quests_v3.quest_progress
                              SET accept_time = $1, start_time = $1, end_time = $1, status = 'completed'
                              WHERE progress_id = $2
                              """,
                              q_v1.accepted_on.isoformat(), progress_id)

        await db.pool.execute("""
                                  UPDATE quests_v3.objective_progress
                                  SET start_time = $1, end_time = $1, status = 'completed'
                                  WHERE progress_id = $2
                              """,
                              q_v1.accepted_on.isoformat(), progress_id)

    v2_quests = await db.pool.fetch("""
                                    select * from quests.quest
                                    """)

    for q_v2 in v2_quests:
        if q_v2["quest_id"] not in v1_quest_memory.keys():
            objectives = await db.pool.fetch("""select * from quests.objective where quest_id = $1""", q_v2["quest_id"])

            obj_create = []
            for obj in objectives:
                rewards = await db.pool.fetch("""select *
                                                    from quests.reward
                                                    where objective_id = $1""", obj["objective_id"])

                rew_create = []
                for rew in rewards:
                    rew_create.append(reward.RewardCreateModel(
                        balance=rew["balance"],
                        item=rew["item"],
                        count=rew["count"],
                        display_name=rew["display_name"],
                        item_metadata=[]
                    ))

                if obj["objective_type"] == 'kill':
                    target = KillTargetModel(target_type='kill', entity=obj["objective"], count=obj["objective_count"])
                elif obj["objective_type"] == 'mine':
                    target = MineTargetModel(target_type='mine', block=obj["objective"], count=obj["objective_count"])
                else:
                    target = EncounterTargetModel(target_type='encounter', script_id=obj["objective"], count=obj["objective_count"])

                customizations = Customizations()

                if obj["required_mainhand"]:
                    customizations.mainhand = MainhandCustomization(item=obj["required_mainhand"])
                if obj["required_location"]:
                    customizations.location = LocationCustomization(
                        coordinates=(obj["required_location"][0], 70, obj["required_location"][1]),
                        horizontal_radius=obj["location_radius"],
                        vertical_radius=obj["location_radius"],
                    )
                if obj["natural_block"]:
                    customizations.natural_block = NaturalBlockCustomization()
                if obj["required_deaths"]:
                    customizations.maximum_deaths = MaximumDeathsCustomization(
                        deaths=obj["required_deaths"],
                        fail=obj["continue_on_fail"]
                    )
                if obj["objective_timer"]:
                    customizations.timer = TimerCustomization(seconds=obj["objective_timer"], fail=obj["continue_on_fail"])

                obj_create.append(objective.ObjectiveCreateModel(
                    description=obj["description"],
                    objective_type=obj["objective_type"],
                    display=obj["display"],
                    order_index=obj["order"],
                    logic="and",
                    target_count=0,
                    rewards=rew_create,
                    targets=[target],
                    customizations=customizations
                ))

            quest_create = quest.QuestCreateModel(
                title=q_v2["title"],
                description=q_v2["description"],
                created_by=q_v2["created_by"],
                tags=q_v2["tags"],
                quest_type=q_v2["quest_type"],
                start_time=q_v2["start_time"],
                end_time=q_v2["end_time"],
                objectives=obj_create
            )

            await quest.QuestModel.create(db, quest_create)

    model = await quest.QuestListModel.fetch(db)
    return sanic.json(model.model_dump(), default=str)
