from flask import Flask, render_template_string, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

# Initializes the Flask app
app = Flask(__name__)

# Configures the SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Defines the Expense model
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rent = db.Column(db.Float, default=0)
    utilities = db.Column(db.Float, default=0)
    food = db.Column(db.Float, default=0)
    transportation = db.Column(db.Float, default=0)
    subscriptions = db.Column(db.Float, default=0)
    savings = db.Column(db.Float, default=0)
    miscellaneous = db.Column(db.Float, default=0)

# Defines the Transaction model
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)

# Initialize the database
with app.app_context():
    db.create_all()
    if not Expense.query.first():
        db.session.add(Expense())
        db.session.commit()

# HTML template for the app's frontend
template = """
<!DOCTYPE html>
<html>
<head>
  <title>SpendRight!</title>
  <script src="https://d3js.org/d3.v7.min.js"></script>
  <style>
    body {
      background-color: lightgrey;
      color: black;
      font-family: Arial, sans-serif;
      text-align: center;
    }
    select, input, button {
      margin: 10px;
      padding: 5px;
    }
    button {
      background-color: white;
      color: green;
      border: none;
      cursor: pointer;
    }
    button:hover {
      background-color: lightgreen;
    }
    #chart {
      margin: 20px auto;
    }
    table {
      margin: 20px auto;
      border-collapse: collapse;
      width: 50%;
    }
    th, td {
      border: 1px solid black;
      padding: 10px;
      text-align: left;
    }
    th {
      background-color: darkgrey;
    }
  </style>
</head>
<body>
  <h1>Welcome to SpendRight!</h1>
  <form method="POST" action="/">
    <select name="category">
      <option value="rent">Rent</option>
      <option value="utilities">Utilities</option>
      <option value="food">Food</option>
      <option value="transportation">Transportation</option>
      <option value="subscriptions">Subscriptions</option>
      <option value="savings">Savings</option>
      <option value="miscellaneous">Miscellaneous</option>
    </select>
    <input type="number" name="value" step="0.01" placeholder="Amount to Add" required>
    <button type="submit">Add</button>
  </form>
  <form method="POST" action="/reset">
    <button type="submit" style="background-color: red; color: white;">Reset All</button>
  </form>
  <h2>Transaction Log</h2>
  <table>
    <thead>
      <tr>
        <th>Category</th>
        <th>Amount</th>
      </tr>
    </thead>
    <tbody>
      {% for transaction in transactions %}
      <tr>
        <td>{{ transaction.category }}</td>
        <td>${{ "%.2f"|format(transaction.amount) }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  <h3>Total Expenses: ${{ "%.2f"|format(total) }}</h3>
  <svg id="chart" width="500" height="500"></svg>
  <script>
    const categories = ["Rent", "Utilities", "Food", "Transportation", "Subscriptions", "Savings", "Miscellaneous"];
    const data = {{ chart_data | safe }};
    function createChart(data) {
      const width = 500, height = 500, radius = Math.min(width, height) / 2;
      const color = d3.scaleOrdinal().domain(categories).range(d3.schemeCategory10);
      d3.select("#chart").selectAll("*").remove();
      const svg = d3.select("#chart").append("g").attr("transform", `translate(${width / 2}, ${height / 2})`);
      const pie = d3.pie().value(d => d);
      const arc = d3.arc().innerRadius(0).outerRadius(radius);
      svg.selectAll("path")
        .data(pie(data))
        .join("path")
        .attr("d", arc)
        .attr("fill", (_, i) => color(categories[i]))
        .append("title")
        .text((d, i) => `${categories[i]}: ${d.data}`);
      svg.selectAll("text")
        .data(pie(data))
        .join("text")
        .attr("transform", d => `translate(${arc.centroid(d)})`)
        .attr("text-anchor", "middle")
        .style("font-size", "12px")
        .style("fill", "white")
        .text((d, i) => `${categories[i]}: ${d.data}`);
    }
    createChart(data);
  </script>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def home():
    expense = Expense.query.first()
    if request.method == "POST" and "category" in request.form and "value" in request.form:
        category = request.form["category"]
        added_value = float(request.form["value"])
        current_value = getattr(expense, category)
        setattr(expense, category, current_value + added_value)
        db.session.add(Transaction(category=category, amount=added_value))
        db.session.commit()
    transactions = Transaction.query.all()
    total = sum(transaction.amount for transaction in transactions)
    chart_data = [
        expense.rent,
        expense.utilities,
        expense.food,
        expense.transportation,
        expense.subscriptions,
        expense.savings,
        expense.miscellaneous,
    ]
    return render_template_string(template, chart_data=chart_data, transactions=transactions, total=total)

@app.route("/reset", methods=["POST"])
def reset():
    expense = Expense.query.first()
    expense.rent = 0
    expense.utilities = 0
    expense.food = 0
    expense.transportation = 0
    expense.subscriptions = 0
    expense.savings = 0
    expense.miscellaneous = 0
    db.session.query(Transaction).delete()
    db.session.commit()
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
