from datetime import date, datetime
from typing import Optional, List
from pydantic import Field
from sanic_ext import openapi
from src.utils.base import BaseModel, BaseList
from src.database import Database
from src.utils.errors import BadRequest400, NotFound404
import json


@openapi.component()
class PlaytimeMetrics(BaseModel):
    total_seconds: Optional[float] = Field(description="Total seconds played this year")
    highest_day: Optional[date] = Field(description="Day with most playtime")
    highest_day_seconds: Optional[float] = Field(description="Seconds played on highest day")
    most_active_hour: Optional[int] = Field(description="Most active hour of day (0-23)")
    most_active_hour_sessions: Optional[int] = Field(description="Session count during most active hour")
    most_active_hour_seconds: Optional[float] = Field(description="Total seconds during most active hour")


@openapi.component()
class QuestMetrics(BaseModel):
    total_accepted: Optional[int] = Field(description="Total quests accepted")
    total_completed: Optional[int] = Field(description="Total quests completed")
    total_failed: Optional[int] = Field(description="Total quests failed")
    completion_rate: Optional[float] = Field(description="Quest completion rate percentage")
    fastest_quest_title: Optional[str] = Field(description="Title of fastest completed quest")
    fastest_quest_start_time: Optional[datetime] = Field(description="Start time of fastest quest")
    fastest_quest_completion_time: Optional[datetime] = Field(description="Completion time of fastest quest")
    fastest_quest_duration_seconds: Optional[float] = Field(description="Duration of fastest quest in seconds")


@openapi.component()
class RewardMetrics(BaseModel):
    total_rewards: Optional[int] = Field(description="Total rewards earned")
    total_balance_earned: Optional[int] = Field(description="Total balance/currency earned")
    total_items_earned: Optional[int] = Field(description="Total item rewards earned")
    unique_items: Optional[int] = Field(description="Unique item types earned")


@openapi.component()
class KillCountModel(BaseModel):
    mob_type: str = Field(description="The mob that was killed")
    kill_count: int = Field(description="The kill count")


@openapi.component()
class FavouriteBlockModel(BaseModel):
    category: str = Field(description="The category of the favourite block, placed or mined")
    month_name: str = Field(description="The month name")
    month_number: int = Field(description="The month number")
    favorite_block: str = Field(description="The favourite block")
    count: int = Field(description="The count of the favourite block")


@openapi.component()
class InteractionMetrics(BaseModel):
    blocks_placed: Optional[int] = Field(description="Total blocks placed")
    blocks_mined: Optional[int] = Field(description="Total blocks mined")
    net_difference: Optional[int] = Field(description="Net block difference (placed - mined)")
    player_type: Optional[str] = Field(description="Player type: Creator, Destroyer, or Balanced Builder")
    arch_nemesis: Optional[str] = Field(description="Mob that killed player the most")
    death_count: Optional[int] = Field(description="Deaths to arch nemesis")
    kill_counts: Optional[List[KillCountModel]] = Field(description="List of mobs killed and their counts")
    block_timeline: Optional[List[FavouriteBlockModel]] = Field(description="Timeline of favorite blocks by month")


@openapi.component()
class ProjectMetrics(BaseModel):
    favourite_project_id: Optional[str] = Field(description="Favorite project ID (most blocks placed)")
    favourite_project_name: Optional[str] = Field(description="Favorite project name")
    favourite_project_blocks_placed: Optional[int] = Field(description="Blocks placed in favorite project")
    most_active_project_id: Optional[str] = Field(description="Most active project ID (total activity)")
    most_active_project_name: Optional[str] = Field(description="Most active project name")
    most_active_project_blocks_placed: Optional[int] = Field(description="Blocks placed in most active project")
    most_active_project_blocks_mined: Optional[int] = Field(description="Blocks mined in most active project")
    most_active_project_interactions: Optional[int] = Field(description="Interactions in most active project")
    most_active_project_total_activity: Optional[int] = Field(description="Total activity in most active project")


@openapi.component()
class GrindDayMetrics(BaseModel):
    grind_date: Optional[date] = Field(description="Peak grind day date")
    sessions: Optional[int] = Field(description="Sessions on grind day")
    hours_played: Optional[float] = Field(description="Hours played on grind day")
    first_login: Optional[datetime] = Field(description="First login on grind day")
    last_logout: Optional[datetime] = Field(description="Last logout on grind day")
    blocks: Optional[int] = Field(description="Total blocks on grind day")
    blocks_placed: Optional[int] = Field(description="Blocks placed on grind day")
    blocks_mined: Optional[int] = Field(description="Blocks mined on grind day")
    mob_kills: Optional[int] = Field(description="Mob kills on grind day")
    interactions: Optional[int] = Field(description="Interactions on grind day")
    quests_completed: Optional[int] = Field(description="Quests completed on grind day")
    total_combined_actions: Optional[int] = Field(description="Total actions on grind day")


@openapi.component()
class FavouritePersonModel(BaseModel):
    other_player_id: int = Field(description="Other player id")
    username: str = Field(description="Username")
    seconds_played_together: float = Field(description="Total seconds played together")


@openapi.component()
class SocialMetrics(BaseModel):
    favourite_people: Optional[List[FavouritePersonModel]] = Field(description="Top 5 people played with most")


@openapi.component()
class EverthornWrapped2025(BaseModel):
    thorny_id: int = Field(description="User's thorny ID")
    username: Optional[str] = Field(description="Username")

    playtime: Optional[PlaytimeMetrics] = Field(description="Playtime statistics")
    quests: Optional[QuestMetrics] = Field(description="Quest statistics")
    rewards: Optional[RewardMetrics] = Field(description="Reward statistics")
    interactions: Optional[InteractionMetrics] = Field(description="Interaction statistics")
    projects: Optional[ProjectMetrics] = Field(description="Project statistics")
    grind_day: Optional[GrindDayMetrics] = Field(description="Peak grind day statistics")
    social: Optional[SocialMetrics] = Field(description="Social statistics")

    @classmethod
    async def fetch(cls, db: Database, thorny_id: int = None, *args) -> "EverthornWrapped2025":
        if not thorny_id:
            raise BadRequest400(extra={'ids': ['thorny_id']})

        data = await db.pool.fetchrow("""
                                          SELECT *
                                          FROM users.everthorn_wrapped_2025
                                          WHERE thorny_id = $1
                                      """, thorny_id)

        if not data:
            raise NotFound404(extra={'resource': 'wrapped_2025', 'id': f'{thorny_id}'})

        # Parse kill counts
        kill_counts_list = []
        if data['kill_mob_types'] and data['kill_counts']:
            for i, mob_type in enumerate(data['kill_mob_types']):
                kill_counts_list.append(KillCountModel(
                    mob_type=mob_type,
                    kill_count=data['kill_counts'][i]
                ))

        block_timeline_list = []
        if data['block_timeline']:
            timeline = json.loads(data['block_timeline'])

            for block_data in timeline:
                block_timeline_list.append(FavouriteBlockModel(
                    category=block_data['category'],
                    month_name=block_data['month_name'],
                    month_number=block_data['month_number'],
                    favorite_block=block_data['favorite_block'],
                    count=block_data['count']
                ))

        # Fetch usernames for favourite people
        favourite_people = []
        if data['top_player_ids'] and data['top_player_seconds']:
            for i, player_id in enumerate(data['top_player_ids']):
                user_data = await db.pool.fetchrow("""
                                                       SELECT username
                                                       FROM users."user"
                                                       WHERE thorny_id = $1
                                                   """, player_id)

                if user_data:
                    favourite_people.append(FavouritePersonModel(
                        other_player_id=player_id,
                        username=user_data['username'],
                        seconds_played_together=round(data['top_player_seconds'][i], 2)
                    ))

        # Map flat database columns to nested structure
        return cls(
            thorny_id=data['thorny_id'],
            username=data['username'],
            playtime=PlaytimeMetrics(
                total_seconds=data['total_seconds'],
                highest_day=data['highest_day'],
                highest_day_seconds=data['highest_day_seconds'],
                most_active_hour=data['most_active_hour'],
                most_active_hour_sessions=data['most_active_hour_sessions'],
                most_active_hour_seconds=data['most_active_hour_seconds']
            ) if data['total_seconds'] else None,
            quests=QuestMetrics(
                total_accepted=data['total_accepted'],
                total_completed=data['total_completed'],
                total_failed=data['total_failed'],
                completion_rate=data['completion_rate'],
                fastest_quest_title=data['fastest_quest_title'],
                fastest_quest_start_time=data['fastest_quest_start_time'],
                fastest_quest_completion_time=data['fastest_quest_completion_time'],
                fastest_quest_duration_seconds=data['fastest_quest_duration_seconds']
            ) if data['total_accepted'] else None,
            rewards=RewardMetrics(
                total_rewards=data['total_rewards'],
                total_balance_earned=data['total_balance_earned'],
                total_items_earned=data['total_items_earned'],
                unique_items=data['unique_items']
            ) if data['total_rewards'] else None,
            interactions=InteractionMetrics(
                blocks_placed=data['blocks_placed'],
                blocks_mined=data['blocks_mined'],
                net_difference=data['net_difference'],
                player_type=data['player_type'],
                arch_nemesis=data['arch_nemesis'],
                death_count=data['death_count'],
                kill_counts=kill_counts_list if kill_counts_list else None,
                block_timeline=block_timeline_list if block_timeline_list else None
            ) if data['blocks_placed'] is not None else None,
            projects=ProjectMetrics(
                favourite_project_id=data['fav_project_id'],
                favourite_project_name=data['fav_project_name'],
                favourite_project_blocks_placed=data['fav_project_blocks_placed'],
                most_active_project_id=data['active_project_id'],
                most_active_project_name=data['active_project_name'],
                most_active_project_blocks_placed=data['active_project_blocks_placed'],
                most_active_project_blocks_mined=data['active_project_blocks_mined'],
                most_active_project_interactions=data['active_project_interactions'],
                most_active_project_total_activity=data['active_project_total_activity']
            ) if data['fav_project_id'] or data['active_project_id'] else None,
            grind_day=GrindDayMetrics(
                grind_date=data['grind_date'],
                sessions=data['grind_sessions'],
                hours_played=data['grind_hours_played'],
                first_login=data['grind_first_login'],
                last_logout=data['grind_last_logout'],
                blocks=data['grind_blocks'],
                blocks_placed=data['grind_blocks_placed'],
                blocks_mined=data['grind_blocks_mined'],
                mob_kills=data['grind_mob_kills'],
                interactions=data['grind_interactions'],
                quests_completed=data['grind_quests_completed'],
                total_combined_actions=data['grind_total_combined_actions']
            ) if data['grind_date'] else None,
            social=SocialMetrics(
                favourite_people=favourite_people if favourite_people else None
            ) if favourite_people else None
        )
