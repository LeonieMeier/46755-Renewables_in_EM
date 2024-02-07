""" Code for the copper-plate system with one hour """

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import gurobipy as gp
GRB = gp.GRB


""" Variables used in the file """
# Informations on generating units are in the dataframe 'Generators' with the columns names :
    # 'Name' for the name of the generator
    # 'Capacity' for the capacity of the generator
    # 'Bid price' for the bid price of the generator
    
# Informations on demanding units are in the dataframe 'Demands' with the columns names :
    # 'Name' for the name of the demand
    # 'Load' for the load of the demand
    # 'Offer price' for the offer price of the demand
    
    
""" Fake Variables defined just for trying the problem """

Generators = pd.DataFrame([
    ['Gas 1',40,80],['Gas 2',25,85],
    ['Coal 1',30,70],['Coal 2',30,65],
    ['Biomass',20,40],['Nuclear',80,20],
    ['Wind 1',20,0],['Wind 2',5,0]],
    columns=['Name','Capacity','Bid price'])
# Order in ascending orders of bid price for easier treatment
Generators = Generators.sort_values(by='Bid price').reset_index(drop=True)

Demands = pd.DataFrame([
    ['Houses',120,120],['Industry 1',50,100],
    ['Industry 2',20,80]],
    columns=['Name','Load','Offer price'])
# Order in descending orders of offer price for easier treatment
Demands = Demands.sort_values(by='Offer price', ascending=False).reset_index(drop=True)


""" Function useful for clearing the market """
        
# Taking the hour supply and load information and optimizing (see lecture 2)
def Single_hour_optimization(Generators, Demands) :
    # Numbers of generators and demanding units
    n_gen = len(Generators)
    n_dem = len(Demands)
    #Create the model
    model = gp.Model()
    #Initialize the decision variables
    var_gen = model.addVars(range(n_gen), vtype=GRB.CONTINUOUS, name='gen')
    var_dem = model.addVars(range(n_dem), vtype=GRB.CONTINUOUS, name='dem')
    #Add constraints to the model
    model.addConstr(gp.quicksum(var_dem[i] for i in range(n_dem)) - gp.quicksum(var_gen[i] for i in range(n_gen)) == 0)
    for i in range(n_gen) :
        model.addConstr(var_gen[i] <= Generators['Capacity'][i])
    for i in range(n_dem) :
        model.addConstr(var_dem[i] <= Demands['Load'][i])
    # Add the objective function to the model
    model.setObjective(gp.quicksum([Demands['Offer price'][i]*var_dem[i] for i in range(n_dem)])-gp.quicksum([Generators['Bid price'][i]*var_gen[i] for i in range(n_gen)]), GRB.MAXIMIZE)
    #Solve the problem
    model.optimize()
    
    # Get the optimal values
    if model.status == GRB.OPTIMAL:
        # Create a list to store the optimal values of the variables
        optimal_gen = [var_gen[i].X for i in range(n_gen)]
        optimal_dem = [var_dem[i].X for i in range(n_dem)]
        # Value of the optimal objective
        optimal_obj = model.ObjVal
        
        # Print
        print("\n")
        print("Power generation :")
        for i, value in enumerate(optimal_gen):
            print(Generators["Name"][i] + f" : {value}")
        print("\n")
        print("Demand provided :")
        for i, value in enumerate(optimal_dem):
            print(Demands["Name"][i] + f" : {value}")
    else:
        print("Optimization did not converge to an optimal solution.")
        
    # Return the cost and the optimal values
    return(optimal_obj, optimal_gen, optimal_dem)
    

# Taking the optimization and giving the clearing price
def Single_hour_price(Generators, Demands, optimal_gen, optimal_dem) :
    # Go through the different suppliers to find the clearing price
    clearing = False
    clearing_price = 0
    i = 0
    while (clearing == False) and (i <= len(Generators)) :
        max_cap = Generators['Capacity'][i]
        eff_cap = optimal_gen[i]
        if eff_cap > 0 and eff_cap < max_cap :
            clearing_price = Generators['Bid price'][i]
            clearing = True
        elif eff_cap == max_cap and i!= len(Generators)-1 :
            next_eff_cap = optimal_gen[i+1]
            if next_eff_cap != 0 :
                clearing_price = Generators['Bid price'][i]
                i += 1
            else :
                next_bid_price = Generators['Bid price'][i+1]
                clearing_price = [clearing_price, next_bid_price]
                clearing = True
        else :
            clearing_price = Generators['Bid price'][i]
            clearing = True
            
    print("\n")
    print(f"Clearing price : {clearing_price} $/MWh")
    print("Quantity provided : " + str(sum(optimal_dem)) + " MW")
    return(clearing_price)


# Plotting the solution of the clearing for an hour and demands and generators entries
def Single_hour_plot(Generators, Demands, clearing_price, optimal_gen, optimal_dem) :
    # Size of the figure
    plt.figure(figsize = (20, 12))
    plt.rcParams["font.size"] = 16
    
    # Different colors for each suppliers
    colors = sns.color_palette('flare', len(Generators))
    # Positions of the suppliers bars
    xpos = [0]
    for i in range(1,len(Generators)) :
        xpos.append(Generators["Capacity"][i-1] + xpos[i-1])
    y = Generators["Bid price"].values.tolist()
    # Width of each suppliers bars
    w = Generators["Capacity"].values.tolist()

    fig = plt.bar(xpos, 
            height = y,
            width = w,
            fill = True,
            color = colors,
            align = 'edge')

    plt.xlim(0, max(Generators["Capacity"].sum(),Demands["Load"].sum()+5))
    plt.ylim(0, max(Generators["Bid price"].max(),Demands["Offer price"].max()) + 15)
    
    plt.legend(fig.patches, Generators["Name"].values.tolist(),
              loc = "best",
              ncol = 3)
    
    
    # Demands
    max_demand = sum(Demands["Load"].values.tolist())
    xpos = 0
    for i in range(len(Demands)) :
        plt.hlines(y = Demands["Offer price"][i],
                  xmin = xpos,
                  xmax = Demands["Load"][i] + xpos,
                  color = "red",
                  linestyle = "dashed")
        xpos = Demands["Load"][i] + xpos
        if i != len(Demands)-1:
            plt.vlines(x = xpos,
                        ymin = Demands["Offer price"].values.tolist()[i+1],
                        ymax = Demands["Offer price"].values.tolist()[i],
                        color = "red",
                        linestyle = "dashed",
                        label = "Demand")
    plt.vlines(x = max_demand,
                ymin = 0,
                ymax = Demands["Offer price"].values.tolist()[-1],
                color = "red",
                linestyle = "dashed",
                label = "Demand")
    
    if type(clearing_price) == list :
        plt.text(x = sum(optimal_gen) - 10,
                y = clearing_price[-1] + 10,
                s = f"Electricity price: \n    {clearing_price} $/MWh \n Quantity : " + str(sum(optimal_dem)) + " MW")
    else :
        plt.text(x = sum(optimal_gen) - 10,
                y = clearing_price + 10,
                s = f"Electricity price: \n    {clearing_price} $/MWh \n Quantity : " + str(sum(optimal_dem)) + "MW")

    plt.xlabel("Power plant capacity (MW)")
    plt.ylabel("Bid price ($/MWh)")
    plt.title("Market clearing for the copper plate single hour")
    plt.show()
    


""" Global function """

def Copper_plate_single_hour(Generators, Demands) :
    # Solving the optimization problem
    optimal_obj, optimal_gen, optimal_dem = Single_hour_optimization(Generators, Demands)
    # Clearing the price
    clearing_price = Single_hour_price(Generators, Demands, optimal_gen, optimal_dem)
    # Plotting the results
    Single_hour_plot(Generators, Demands, clearing_price, optimal_gen, optimal_dem)
    
Copper_plate_single_hour(Generators, Demands)

















        

