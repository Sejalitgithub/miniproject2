from flask import Flask, render_template, request
import pandas as pd

from random import uniform as rnd

app = Flask(__name__)

nutritions_values = ['Calories', 'FatContent', 'SaturatedFatContent', 'CholesterolContent', 'SodiumContent',
                     'CarbohydrateContent', 'FiberContent', 'SugarContent', 'ProteinContent']

# Load the dataset
dataset = pd.read_csv("dataset.csv")

class Person:
    def __init__(self, age, height, weight, gender, activity, meals_calories_perc, weight_loss):
        self.age = age
        self.height = height
        self.weight = weight
        self.gender = gender
        self.activity = activity
        self.meals_calories_perc = meals_calories_perc
        self.weight_loss = weight_loss

    def calculate_bmi(self):
        bmi = round(self.weight / ((self.height / 100) ** 2), 2)
        return bmi

    def calculate_bmr(self):
        if self.gender == 'Male':
            bmr = 10 * self.weight + 6.25 * self.height - 5 * self.age + 5
        else:
            bmr = 10 * self.weight + 6.25 * self.height - 5 * self.age - 161
        return bmr

    def calories_calculator(self):
        activities = ['Little/no exercise', 'Light exercise', 'Moderate exercise (3-5 days/wk)',
                      'Very active (6-7 days/wk)', 'Extra active (very active & physical job)']
        weights = [1.2, 1.375, 1.55, 1.725, 1.9]
        weight = weights[activities.index(self.activity)]
        maintain_calories = self.calculate_bmr() * weight
        return maintain_calories

    def generate_recommendations(self):
        total_calories = self.weight_loss * self.calories_calculator()
        recommendations = []
        for meal in self.meals_calories_perc:
            meal_calories = self.meals_calories_perc[meal] * total_calories
            filtered_recipes = dataset[(dataset['Calories'] >= meal_calories * 0.8) &
                                       (dataset['Calories'] <= meal_calories * 1.2)]
            if not filtered_recipes.empty:
                selected_recipe = filtered_recipes.sample()
                recommended_nutrition = selected_recipe.iloc[0]
                recommendations.append(recommended_nutrition)
            else:
                recommendations.append(pd.Series(["No Recipe Found"] * len(dataset.columns), index=dataset.columns))
        return recommendations


class Display:
    def display_bmi(self, person):
        bmi = person.calculate_bmi()
        bmi_string = f'{bmi} kg/m²'
        return bmi_string

    def display_calories(self, person):
        maintain_calories = person.calories_calculator()
        return round(maintain_calories)

    def display_recommendation(self, recommendations, person=None):
        recipe_info = []
        for meal_name, recommendation in zip(person.meals_calories_perc, recommendations):
            if recommendation.iloc[0] == "No Recipe Found":
                recipe_info.append((meal_name, "No recipe found matching the calorie range."))
            else:
                recipe_name = recommendation['Name']
                recipe_nutrition = recommendation[nutritions_values]
                recipe_info.append((meal_name, recipe_name, recipe_nutrition))
        return recipe_info
#second

def clean_ingredients(ingredients):
    if isinstance(ingredients, str):
        # Remove leading 'c(' and trailing ')'
        ingredients = ingredients.strip('c(').strip(')')
        # Split by ',' and remove leading and trailing whitespace
        ingredients_list = [ingredient.strip().strip('"') for ingredient in ingredients.split('", "')]
        return ingredients_list
    else:
        return []

def clean_instructions(instructions):
    if isinstance(instructions, str):
        # Remove leading 'c(' and trailing ')'
        instructions = instructions.strip('c(').strip(')')
        # Split by '|' and remove leading and trailing whitespace
        instructions_list = [instruction.strip().strip('"') for instruction in instructions.split('", "')]
        return instructions_list
    else:
        return []

def recommend_popular_recipes(n_recommendations):
    if 'Images' in dataset.columns:
        data_filtered = dataset[dataset['Images'] != 'character(0)']
        popular_recipes = data_filtered.nlargest(n_recommendations, 'AggregatedRating')
        popular_recipes['Images'] = popular_recipes['Images'].apply(lambda x: x.strip('c("').strip('")').split('", "'))
        # Clean RecipeIngredientParts column
        popular_recipes['RecipeIngredientParts'] = popular_recipes['RecipeIngredientParts'].apply(clean_ingredients)
        # Clean RecipeInstructions column
        popular_recipes['RecipeInstructions'] = popular_recipes['RecipeInstructions'].apply(clean_instructions)
        return popular_recipes[['RecipeId', 'Name', 'CookTime', 'PrepTime', 'TotalTime', 'RecipeIngredientQuantities', 'RecipeIngredientParts', 'RecipeInstructions', 'Images']]
    else:
        return pd.DataFrame()

def recommend_recipes_by_name(food_name, n_recommendations):
    if 'Images' in dataset.columns:
        data_filtered = dataset[dataset['Images'] != 'character(0)']
        name_recipes = data_filtered[data_filtered['Name'].str.contains(food_name, case=False, na=False)]
        name_recipes['Images'] = name_recipes['Images'].apply(lambda x: x.strip('c("').strip('")').split('", "'))
        # Clean RecipeIngredientParts column
        name_recipes['RecipeIngredientParts'] = name_recipes['RecipeIngredientParts'].apply(clean_ingredients)
        # Clean RecipeInstructions column
        name_recipes['RecipeInstructions'] = name_recipes['RecipeInstructions'].apply(clean_instructions)
        return name_recipes.sample(n=min(n_recommendations, len(name_recipes)))
    else:
        return pd.DataFrame()

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/recommendation', methods=['GET', 'POST'])
@app.route('/recommendation', methods=['POST'])
def recommendation_route():  # Change the function name to avoid conflicts
    age = int(request.form['age'])
    height = int(request.form['height'])
    weight = int(request.form['weight'])
    gender = request.form['gender']
    activity = request.form['activity']
    weight_loss_option = request.form['weight_loss_option']
    number_of_meals = int(request.form['number_of_meals'])

    # Calculate meals_calories_perc based on the number_of_meals
    if number_of_meals == 3:
        meals_calories_perc = {'breakfast': 0.3, 'lunch': 0.4, 'dinner': 0.3}
    elif number_of_meals == 4:
        meals_calories_perc = {'breakfast': 0.25, 'lunch': 0.35, 'dinner': 0.3, 'snack': 0.1}
    else:  # Assuming number_of_meals == 5
        meals_calories_perc = {'breakfast': 0.2, 'lunch': 0.3, 'dinner': 0.25, 'snack1': 0.1, 'snack2': 0.15}

    # Determine the weight_loss based on the weight_loss_option
    if weight_loss_option == 'Maintain weight':
        weight_loss = 1.0
    elif weight_loss_option == 'Mild weight loss':
        weight_loss = 0.95
    elif weight_loss_option == 'Weight loss':
        weight_loss = 0.9
    else:  # Assuming weight_loss_option == 'Extreme weight loss'
        weight_loss = 0.85

    person = Person(age, height, weight, gender, activity, meals_calories_perc, weight_loss)
    display = Display()
    bmi = display.display_bmi(person)
    calories = display.display_calories(person)
    recommendations = person.generate_recommendations()
    recipe_info = display.display_recommendation(recommendations, person)

    return render_template('recommendation.html', bmi=bmi, calories=calories, recommendations=recipe_info)



@app.route('/recommend', methods=['POST'])
def recommend():
    n_recommendations = 5
    food_name = request.form['keywords']
    popular_recipes = recommend_popular_recipes(n_recommendations)
    name_recipes = recommend_recipes_by_name(food_name, n_recommendations)
    return render_template('rcom.html', popular_recipes=popular_recipes, name_recipes=name_recipes)

@app.route('/recom')
def home2():
    return render_template('index2.html')


if __name__ == '__main__':
    app.run(debug=True, port=5001)