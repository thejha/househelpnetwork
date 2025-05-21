import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import func, desc
from app import app, db
from models import HelperProfile, Review, Contract, ReviewTaskRating, TaskList

def generate_helper_analytics():
    """Generate analytics reports for helpers performance"""
    with app.app_context():
        print("Generating Helper Analytics Report...")
        
        # Get all helpers with their review data
        helpers = HelperProfile.query.all()
        
        analytics_data = []
        
        for helper in helpers:
            # Get all reviews for this helper
            reviews = Review.query.filter_by(helper_profile_id=helper.id).all()
            
            # Skip helpers with no reviews
            if not reviews:
                continue
                
            # Calculate average ratings
            avg_punctuality = sum(r.punctuality for r in reviews) / len(reviews)
            avg_attitude = sum(r.attitude for r in reviews) / len(reviews)
            avg_hygiene = sum(r.hygiene for r in reviews) / len(reviews)
            avg_reliability = sum(r.reliability for r in reviews) / len(reviews)
            avg_communication = sum(r.communication for r in reviews) / len(reviews)
            avg_overall = sum(r.overall_rating for r in reviews) / len(reviews)
            
            # Get task ratings details
            task_ratings = {}
            for review in reviews:
                for tr in review.task_ratings:
                    task_name = tr.task.name
                    if task_name not in task_ratings:
                        task_ratings[task_name] = []
                    task_ratings[task_name].append(tr.rating)
            
            # Calculate average for each task
            avg_task_ratings = {}
            for task_name, ratings in task_ratings.items():
                avg_task_ratings[task_name] = sum(ratings) / len(ratings)
            
            # Get location data
            city = helper.city or "Unknown"
            state = helper.state or "Unknown"
            location = f"{city}, {state}"
            
            # Add to analytics data
            helper_data = {
                'helper_id': helper.helper_id,
                'name': helper.name,
                'helper_type': helper.helper_type,
                'location': location,
                'city': city,
                'state': state,
                'reviews_count': len(reviews),
                'avg_punctuality': round(avg_punctuality, 2),
                'avg_attitude': round(avg_attitude, 2),
                'avg_hygiene': round(avg_hygiene, 2),
                'avg_reliability': round(avg_reliability, 2),
                'avg_communication': round(avg_communication, 2),
                'avg_overall': round(avg_overall, 2),
                'task_ratings': avg_task_ratings
            }
            
            analytics_data.append(helper_data)
        
        # Convert to DataFrame for analysis
        if analytics_data:
            df = pd.DataFrame(analytics_data)
            
            # Sort by overall rating
            df = df.sort_values('avg_overall', ascending=False)
            
            # Print top 5 helpers overall
            print("\nTop 5 Helpers Overall:")
            top_helpers = df[['name', 'helper_type', 'location', 'avg_overall', 'reviews_count']].head(5)
            print(top_helpers)
            
            # Group by helper type and find top performers
            print("\nTop Performers by Helper Type:")
            for helper_type, group in df.groupby('helper_type'):
                top = group.sort_values('avg_overall', ascending=False).head(3)
                print(f"\n{helper_type.capitalize()}:")
                print(top[['name', 'location', 'avg_overall', 'reviews_count']])
            
            # Group by location and find top performers
            print("\nTop Performers by City:")
            for city, group in df.groupby('city'):
                if len(group) > 1:  # Only show if we have multiple helpers in this city
                    top = group.sort_values('avg_overall', ascending=False).head(3)
                    print(f"\n{city}:")
                    print(top[['name', 'helper_type', 'avg_overall', 'reviews_count']])
            
            # Analyze by core value
            print("\nBest Helpers by Core Value:")
            core_values = ['avg_punctuality', 'avg_attitude', 'avg_hygiene', 
                          'avg_reliability', 'avg_communication']
            
            for value in core_values:
                value_name = value.replace('avg_', '').capitalize()
                top = df.sort_values(value, ascending=False).head(3)
                print(f"\nTop 3 in {value_name}:")
                print(top[['name', 'helper_type', 'location', value, 'avg_overall']])
            
            # For cleaning helpers, find the best by city
            if 'maid' in df['helper_type'].values:
                cleaning_helpers = df[df['helper_type'] == 'maid']
                print("\nBest Cleaning Helpers by City:")
                for city, group in cleaning_helpers.groupby('city'):
                    if not group.empty:
                        top = group.sort_values('avg_overall', ascending=False).head(1)
                        print(f"{city}: {top.iloc[0]['name']} - {top.iloc[0]['avg_overall']}/5")
            
            # Create visualizations
            try:
                # Helper type distribution
                type_counts = df['helper_type'].value_counts()
                plt.figure(figsize=(10, 6))
                type_counts.plot(kind='bar', color='skyblue')
                plt.title('Helper Distribution by Type')
                plt.ylabel('Number of Helpers')
                plt.tight_layout()
                plt.savefig('static/analytics/helper_type_distribution.png')
                
                # Geographical distribution
                city_counts = df['city'].value_counts().head(10)
                plt.figure(figsize=(12, 6))
                city_counts.plot(kind='bar', color='lightgreen')
                plt.title('Helper Distribution by City (Top 10)')
                plt.ylabel('Number of Helpers')
                plt.tight_layout()
                plt.savefig('static/analytics/helper_city_distribution.png')
                
                # Average ratings by helper type
                plt.figure(figsize=(14, 8))
                helper_types = df['helper_type'].unique()
                labels = ['Punctuality', 'Attitude', 'Hygiene', 'Reliability', 'Communication', 'Overall']
                
                x = range(len(labels))
                width = 0.8 / len(helper_types)
                
                for i, htype in enumerate(helper_types):
                    subset = df[df['helper_type'] == htype]
                    means = [
                        subset['avg_punctuality'].mean(),
                        subset['avg_attitude'].mean(), 
                        subset['avg_hygiene'].mean(),
                        subset['avg_reliability'].mean(),
                        subset['avg_communication'].mean(),
                        subset['avg_overall'].mean()
                    ]
                    plt.bar([p + width*i for p in x], means, width, label=htype.capitalize())
                
                plt.xlabel('Rating Category')
                plt.ylabel('Average Rating')
                plt.title('Average Ratings by Helper Type')
                plt.xticks([p + width for p in x], labels)
                plt.legend()
                plt.tight_layout()
                plt.savefig('static/analytics/ratings_by_helper_type.png')
                
                print("\nAnalytics visualizations saved to static/analytics/ directory")
            except Exception as e:
                print(f"Error generating visualizations: {str(e)}")
            
            # Save to CSV for further analysis
            df.to_csv('static/analytics/helper_analytics.csv', index=False)
            print("\nAnalytics data saved to static/analytics/helper_analytics.csv")
        else:
            print("No analytics data available. Ensure there are helpers with reviews in the database.")

if __name__ == "__main__":
    # Create analytics directory if it doesn't exist
    import os
    os.makedirs('static/analytics', exist_ok=True)
    
    # Generate analytics
    generate_helper_analytics() 