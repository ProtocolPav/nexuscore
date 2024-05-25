from typing import Optional, Self

from src.database import Database
from src.models.quest import QuestModel, RewardModel, ObjectiveModel, QuestCreateModel, ObjectiveCreateModel

from pydantic import BaseModel, model_serializer


class QuestView(BaseModel):
    quest: QuestModel
    rewards: Optional[list[RewardModel]]
    objectives: Optional[list[ObjectiveModel]]

    @classmethod
    async def build(cls, db: Database, quest_id: int) -> "QuestView":
        quest = await QuestModel.fetch(db, quest_id)
        all_rewards = await RewardModel.get_all_rewards(db, quest_id)
        all_objectives = await ObjectiveModel.get_all_objectives(db, quest_id)

        rewards = []
        for r_id in all_rewards:
            rewards.append(await RewardModel.fetch(db, r_id))

        objectives = []
        for obj_id in all_objectives:
            objectives.append(await ObjectiveModel.fetch(db, obj_id))

        objectives.sort(key=lambda x: x.order)

        return cls(quest=quest, rewards=rewards, objectives=objectives)

    @model_serializer
    def serialize_for_output(self):
        quest = self.quest.model_dump()
        rewards = {'rewards': [r.model_dump() for r in self.rewards] if self.rewards else None}
        objectives = {'objectives': [o.model_dump() for o in self.objectives] if self.objectives else None}

        return quest | rewards | objectives

    @classmethod
    def view_schema(cls):
        class Schema(QuestModel):
            rewards: list[RewardModel]
            objectives: list[ObjectiveModel]

        return Schema.model_json_schema(ref_template="#/components/schemas/{model}")

    @classmethod
    async def new(cls, db: Database, create_view: "QuestCreateView"):
        quest_model = create_view.quest

        async with db.pool.acquire() as conn:
            async with conn.transaction():
                quest_id = await conn.fetchrow("""
                                                with quest_table as (
                                                    insert into quests.quest(start_time, end_time, timer, title, description)
                                                    values($1, $2, $3, $4, $5)
                
                                                    returning quest_id
                                                )
                                                select quest_id as id from quest_table
                                               """,
                                               quest_model.start_time, quest_model.end_time, quest_model.timer,
                                               quest_model.title, quest_model.description)

                if quest_model.rewards:
                    for reward in quest_model.rewards:
                        await conn.execute("""
                                           INSERT INTO quests.reward(quest_id, balance, item, count)
                                           VALUES($1, $2, $3, $4)
                                           """,
                                           quest_id['id'], reward.balance, reward.item, reward.count)

                objective_model = create_view.objectives
                for objective in objective_model:
                    objective_id = await conn.fetchrow("""
                                                        with objective_table as (
                                                            insert into quests.objective(quest_id,
                                                                                         objective,
                                                                                         objective_count,
                                                                                         objective_type,
                                                                                         objective_timer,
                                                                                         required_mainhand,
                                                                                         required_location,
                                                                                         location_radius,
                                                                                         "order")
                                                            values($1, $2, $3, $4, $5, $6, $7, $8, $9)
        
                                                            returning objective_id
                                                        )
                                                        select objective_id as id from objective_table
                                                       """,
                                                       quest_id['id'], objective.objective, objective.objective_count,
                                                       objective.objective_type, objective.objective_timer,
                                                       objective.required_mainhand, objective.required_location,
                                                       objective.location_radius, objective.order)

                    if objective.rewards:
                        for reward in objective.rewards:
                            await conn.execute("""
                                               INSERT INTO quests.reward(quest_id, objective_id, balance, item, count)
                                               VALUES($1, $2, $3, $4, $5)
                                               """,
                                               quest_id['id'], objective_id['id'], reward.balance, reward.item, reward.count)


class QuestCreateView(BaseModel):
    quest: QuestCreateModel
    objectives: Optional[list[ObjectiveCreateModel]]

    @classmethod
    def view_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")
