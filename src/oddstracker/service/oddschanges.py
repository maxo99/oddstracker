import logging

from oddstracker.service import PG_CLIENT

logger = logging.getLogger(__name__)


def _has_changed(current_outcomes: list[dict], previous_outcomes: list[dict]) -> bool:
    if len(current_outcomes) != len(previous_outcomes):
        return True

    for curr_outcome in current_outcomes:
        curr_changed_date = curr_outcome.get("changedDate")
        outcome_label = curr_outcome.get("label")

        prev_outcome = next(
            (o for o in previous_outcomes if o.get("label") == outcome_label),
            None
        )

        if prev_outcome is None:
            return True

        prev_changed_date = prev_outcome.get("changedDate")

        if curr_changed_date != prev_changed_date:
            return True

    return False


async def get_all_changes():
    logger.info("Fetching all bet offer changes across events")
    events = await PG_CLIENT.get_events()

    changes_by_event = []

    for event in events:
        logger.info(f"Processing changes for event {event}")
        bet_offers = await PG_CLIENT.get_bet_offers_for_event(event.id)

        unique_bet_offer_ids = list({bo.id for bo in bet_offers})

        event_changes = {
            "eventId": event.id,
            "eventName": event.name,
            "changeTimestamps": [],
            "betOffers": []
        }

        for bet_offer_id in unique_bet_offer_ids:
            history = await PG_CLIENT.get_bet_offer_history(bet_offer_id, event.id, limit=2)

            if len(history) < 2:
                logger.info(f"Bet offer {bet_offer_id} has only {len(history)} collection(s), skipping")
                continue

            current = history[0]
            previous = history[1]

            if not _has_changed(current.outcomes, previous.outcomes):
                logger.info(f"Bet offer {bet_offer_id} has not changed")
                continue

            logger.info(f"Bet offer {bet_offer_id} has changed")

            bet_offer_data = {
                "betOfferType": current.type,
                "criterion": current.criterion,
                "collectedAt": current.collected_at.isoformat(),
                "outcomes": []
            }

            for outcome in current.outcomes:
                changed_date = outcome.get("changedDate")
                outcome_data = {
                    "name": outcome.get("name"),
                    "changedDate": changed_date,
                    "odds": outcome.get("odds"),
                    "line": outcome.get("line"),
                    "status": outcome.get("status")
                }

                bet_offer_data["outcomes"].append(outcome_data)

                if changed_date and changed_date not in event_changes["changeTimestamps"]:
                    event_changes["changeTimestamps"].append(changed_date)

            event_changes["betOffers"].append(bet_offer_data)

        if event_changes["betOffers"]:
            event_changes["changeTimestamps"].sort()
            changes_by_event.append(event_changes)
        else:
            logger.debug(f"No changes found for event {event.id}")

    logger.info(f"Processed changes for {len(events)} events, found changes in {len(changes_by_event)} events")
    return changes_by_event

