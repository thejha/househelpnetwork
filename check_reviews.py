from app import app
from models import HelperProfile, Review, ReviewTaskRating

with app.app_context():
    # Find the helper by name
    helper = HelperProfile.query.filter_by(name='Megha Jha').first()
    
    if helper:
        print(f"Found helper: {helper.name} (ID: {helper.id})")
        
        # Get reviews for this helper
        reviews = Review.query.filter_by(helper_profile_id=helper.id).all()
        print(f"Number of reviews: {len(reviews)}")
        
        # Print details of each review
        for r in reviews:
            print(f"Review ID: {r.review_id}")
            print(f"  Punctuality: {r.punctuality}")
            print(f"  Attitude: {r.attitude}")
            print(f"  Hygiene: {r.hygiene}")
            print(f"  Reliability: {r.reliability}")
            print(f"  Communication: {r.communication}")
            
            # Get task ratings for this review
            task_ratings = ReviewTaskRating.query.filter_by(review_id=r.id).all()
            print(f"  Number of task ratings: {len(task_ratings)}")
            
            if task_ratings:
                print("  Task ratings:")
                task_points = 0
                for tr in task_ratings:
                    print(f"    Task ID: {tr.task_id}, Rating: {tr.rating}")
                    task_points += tr.rating
                print(f"  Total task points: {task_points}")
            else:
                print("  No task ratings")
                task_points = 0
            
            # Calculate the overall rating manually
            params_count = 5  # Core values
            task_count = len(task_ratings)
            total_params = params_count + task_count
            
            core_points = r.punctuality + r.attitude + r.hygiene + r.reliability + r.communication
            total_points = core_points + task_points
            
            # Formula: (Total points / (Total parameters × 5)) × 5
            max_possible = total_params * 5
            manual_rating = (total_points / max_possible) * 5 if max_possible > 0 else 0
            
            print(f"  Core values points: {core_points}")
            print(f"  Total points: {total_points}")
            print(f"  Total parameters: {total_params}")
            print(f"  Max possible points: {max_possible}")
            print(f"  Manually calculated rating: {manual_rating:.2f}")
            print(f"  Overall rating from property: {r.overall_rating:.2f}")
            print("-----")
            
        # Calculate helper's average rating from reviews
        if reviews:
            total_rating = sum(r.overall_rating for r in reviews)
            avg_rating = total_rating / len(reviews)
            print(f"\nHelper average rating: {avg_rating:.2f}")
    else:
        print("Helper 'Megha Jha' not found.") 