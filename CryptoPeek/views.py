import datetime
import math
from django.contrib.auth import login, authenticate, logout
from plotly.offline import plot
from plotly.graph_objs import Scatter, Figure, layout, Bar
from django.shortcuts import render, redirect
from requests import get
import pymongo
from .forms import CryptoListForm, SignUpForm, SignInForm, CompareForm

connectionLink = 'mongodb+srv://dgrzesik:cryptopeekdgrzesik@cluster0.r6kad.mongodb.net/CryptoPeek?retryWrites=true&w=majority'
my_client = pymongo.MongoClient(connectionLink)
dbname = my_client['CryptoPeek']
user_favourites = dbname['User_Favourites']


def filter_data(name, input_dict, from_price, to_price, sort_type):
    if from_price:
        input_dict = [x for x in input_dict if x['current_price'] >= from_price]
    if to_price:
        input_dict = [x for x in input_dict if to_price >= x['current_price']]
    if name:
        input_dict = [x for x in input_dict if name.lower() in x['name'].lower()]
    if sort_type == "A-Z":
        input_dict.sort(key=lambda x: x["id"])
    if sort_type == "Z-A":
        input_dict.sort(key=lambda x: x["id"], reverse=True)
    if sort_type == "ArrowDown":
        input_dict.sort(key=lambda x: x["current_price"], reverse=True)
    if sort_type == "ArrowUp":
        input_dict.sort(key=lambda x: x["current_price"])
    if sort_type == "ArrowUpMC":
        input_dict.sort(key=lambda x: x["market_cap"])
    if sort_type == "ArrowDownMC":
        input_dict.sort(key=lambda x: x["market_cap"], reverse=True)
    if sort_type == "ArrowUpPC":
        input_dict.sort(key=lambda x: x["price_change_24h"])
    if sort_type == "ArrowDownPC":
        input_dict.sort(key=lambda x: x["price_change_24h"], reverse=True)
    return input_dict


def getgraphdata(days, crypto_id, all_crypto, graphdata):
    prices = []
    dates = []
    curr_date = datetime.datetime.now() - datetime.timedelta(days)
    first_date = curr_date
    for crypto in all_crypto:
        if crypto["id"] == crypto_id:
            crypto["circulating_supply"] = int(crypto["circulating_supply"])
    if days == 1:
        for value in graphdata["prices"]:
            prices.append(value[1])
            dates.append(curr_date)
            curr_date = curr_date + datetime.timedelta(1 / 24)
    elif days == 365:
        for value in graphdata["prices"]:
            prices.append(value[1])
            dates.append(curr_date)
            curr_date = curr_date + datetime.timedelta(1)
    else:
        for value in graphdata["prices"]:
            prices.append(value[1])
            dates.append(curr_date)
            curr_date = curr_date + datetime.timedelta(1)
    return prices, dates, first_date


def register(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if request.POST['action'] == 'Sign up':
            if form.is_valid():
                user = form.save()
                user.refresh_from_db()
                user.save()
                password = form.cleaned_data['password1']
                user = authenticate(username=user.username, password=password)
                login(request, user)
                user_favourites.insert_one({"username": user.username, "favourites": []})
                return redirect('/cryptopeek/currencies/')
    else:
        form = SignUpForm()
    return render(request, 'CryptoPeek/register.html', {'form': form})


def account(request):
    if request.method == 'POST':
        form = SignInForm(request.POST)
        if request.POST['action'] == 'Sign up':
            return redirect('/cryptopeek/register/')
        if request.POST['action'] == 'Log in':
            if form.is_valid():
                user = form.login(request)
                login(request, user)
                if "favourite" in request.path:
                    return redirect("/cryptopeek/favourite/")
                else:
                    return redirect("/cryptopeek/currencies/")
        if request.POST['action'] == 'Log out':
            logout(request)
            return redirect('/cryptopeek/currencies/')
    else:
        form = SignInForm()
    return render(request, 'CryptoPeek/account.html', {'form': form})


def delete(request, crypto_id):
    user_favourites.update_one({'username': request.user.username}, {"$pull": {'favourites': crypto_id}})
    return redirect('/cryptopeek/favourite')


def compare(request):
    if request.method == 'POST':
        form = CompareForm(request.POST)
        if 'action' in request.POST:
            action = request.POST['action']
        else:
            action = False
        if form.is_valid():
            crypto1 = None
            crypto2 = None
            if action == 'Compare':
                crypto1 = form.cleaned_data["crypto1"]
                crypto2 = form.cleaned_data["crypto2"]
            all_crypto = get(
                'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&sparkline=false').json()
            if crypto1 and crypto2:
                about_crypto1 = [x for x in all_crypto if crypto1.lower() in x['name'].lower()]
                about_crypto2 = [x for x in all_crypto if crypto2.lower() in x['name'].lower()]
                if about_crypto1 != [] and about_crypto2 != []:
                    about_crypto1 = about_crypto1[0]
                    about_crypto2 = about_crypto2[0]
                    month_data_crypto1 = get(
                        'https://api.coingecko.com/api/v3/coins/%s/market_chart?vs_currency=usd&days=%d&interval=daily' % (
                            about_crypto1["id"], 30)).json()
                    prices_crypto1, dates_crypto1, dates_day1_crypto1 = getgraphdata(30, crypto1, all_crypto,
                                                                                     month_data_crypto1)
                    month_data_crypto2 = get(
                        'https://api.coingecko.com/api/v3/coins/%s/market_chart?vs_currency=usd&days=%d&interval=daily' % (
                            about_crypto2["id"], 30)).json()
                    prices_crypto2, dates_crypto2, dates_day1_crypto2 = getgraphdata(30, crypto2, all_crypto,
                                                                                     month_data_crypto2)
                    fig = Figure()
                    fig.add_trace(
                        Scatter(arg=dict(visible=True, name=about_crypto1['name'], x=dates_crypto1, y=prices_crypto1,
                                         mode='markers+lines', opacity=0.8,
                                         marker_color='blue', yaxis="y")))
                    fig.add_trace(
                        Scatter(
                            arg=dict(visible=True, name=about_crypto2['name'], x=dates_crypto2, y=prices_crypto2,
                                     mode='markers+lines', opacity=0.8,
                                     marker_color='red', yaxis="y2")))
                    fig.add_trace(
                        Bar(arg=dict(visible=False, name=about_crypto1['name'], x=dates_crypto1, y=prices_crypto1,
                                     opacity=0.8,
                                     marker_color='blue', yaxis="y")))
                    fig.add_trace(
                        Bar(
                            arg=dict(visible=False, name=about_crypto2['name'], x=dates_crypto2, y=prices_crypto2,
                                     opacity=0.8,
                                     marker_color='red', yaxis="y2")))

                    fig.update_layout(xaxis_title="Dates", width=1100, height=600,
                                      title="Last month's price change comparison",
                                      yaxis=dict(title=about_crypto1['name'], titlefont=dict(color="blue"),
                                                 tickfont=dict(color="blue")),
                                      yaxis2=dict(title=about_crypto2['name'], titlefont=dict(color="red"),
                                                  tickfont=dict(color="red"), anchor="x", automargin=True,
                                                  overlaying="y",
                                                  side="right"),
                                      updatemenus=[layout.Updatemenu(
                                          active=0,
                                          buttons=[dict(label="Compare",
                                                        method='update',
                                                        args=[{'visible': [True, True, False, False]},
                                                              {"yaxis.visible": True, "yaxis2.visible": True,
                                                               'title': "Last month's price change comparison",
                                                               "yaxis2.side": "right", "yaxis.autorange": True,
                                                               "yaxis2.autorange": True}]),
                                                   dict(label=about_crypto1['name'],
                                                        method='update',
                                                        args=[{'visible': [False, False, True, False]},
                                                              {"yaxis.visible": True, "yaxis2.visible": False,
                                                               'title': about_crypto1['name'],
                                                               "yaxis2.side": "right",
                                                               "yaxis.range": [
                                                                   min(prices_crypto1) - (0.01 * min(prices_crypto1)),
                                                                   max(prices_crypto1) + (
                                                                           0.01 * min(prices_crypto1))],
                                                               "yaxis2.range": [
                                                                   min(prices_crypto2) - (0.01 * min(prices_crypto2)),
                                                                   max(prices_crypto2) + (
                                                                           0.01 * min(prices_crypto2))]}]),
                                                   dict(label=about_crypto2['name'],
                                                        method='update',
                                                        args=[{'visible': [False, False, False, True]},
                                                              {"yaxis.visible": False, "yaxis2.visible": True,
                                                               'title': about_crypto2['name'],
                                                               "yaxis2.side": "left",
                                                               "yaxis.range": [
                                                                   min(prices_crypto1) - (0.01 * min(prices_crypto1)),
                                                                   max(prices_crypto1) + (
                                                                           0.01 * min(prices_crypto1))],
                                                               "yaxis2.range": [
                                                                   min(prices_crypto2) - (0.01 * min(prices_crypto2)),
                                                                   max(prices_crypto2) + (
                                                                           0.01 * min(prices_crypto2))]}])
                                                   ])])
                    plot_div = plot(fig, output_type='div')
                    return render(request, 'CryptoPeek/compare.html',
                                  {"currency1": about_crypto1, "currency2": about_crypto2, "plot_div": plot_div,
                                   "form": form})
                return render(request, 'CryptoPeek/compare.html',
                              {"currency1": False, "currency2": False, "form": form})
        if action == 'Log out':
            logout(request)
            return redirect('/cryptopeek/compare/')
        return render(request, 'CryptoPeek/compare.html', {"currency1": False, "currency2": False, "form": form})
    else:
        form = CompareForm()
    return render(request, 'CryptoPeek/compare.html', {"currency1": False, "currency2": False, "form": form})


def favourite(request):
    if request.user.is_authenticated:
        all_crypto = get(
            'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&sparkline=false').json()
        current_user_fav = user_favourites.find_one({'username': request.user.username})['favourites']
        all_crypto = [x for x in all_crypto if x['id'] in current_user_fav]
        if request.method == 'POST':
            form = CryptoListForm(request.POST)
            if 'action' in request.POST:
                action = request.POST['action']
            else:
                action = False
            if request.POST['action'] == 'Log out':
                logout(request)
                return redirect('/cryptopeek/favourite/login/')

            if action == "Search":
                all_crypto = get(
                    'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&sparkline=false').json()
                if form.is_valid():
                    name = form.cleaned_data['name']
                    from_price = form.cleaned_data['from_price']
                    to_price = form.cleaned_data['to_price']
                    sort_type = form.cleaned_data['sort']
                    this_users_fav = user_favourites.find_one({'username': request.user.username})['favourites']
                    all_crypto = [x for x in all_crypto if x['id'] in this_users_fav]
                    input_dict = all_crypto
                    input_dict = filter_data(name, input_dict, from_price, to_price, sort_type)

                    return render(request, 'CryptoPeek/favourite.html', {'all_crypto': input_dict, 'form': form})

        else:
            form = CryptoListForm()
        return render(request, 'CryptoPeek/favourite.html', {'all_crypto': all_crypto, "form": form})
    else:
        return redirect('/cryptopeek/favourite/login/')


def home(request):
    if request.method == 'POST':
        if request.POST['action'] == 'Log out':
            logout(request)
            return redirect('/cryptopeek/home/')
    all_crypto = get(
        'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&sparkline=false').json()
    highest_profit = -math.inf
    lowest_profit = math.inf
    highest_profit_crypto_id = ""
    lowest_profit_crypto_id = ""
    for crypto in all_crypto:
        if crypto["price_change_percentage_24h"] > highest_profit:
            highest_profit = crypto["price_change_percentage_24h"]
            highest_profit_crypto_id = crypto["id"]
        if crypto["price_change_percentage_24h"] < lowest_profit:
            lowest_profit = crypto["price_change_percentage_24h"]
            lowest_profit_crypto_id = crypto["id"]
    highest_profit_data = get('https://api.coingecko.com/api/v3/coins/%s' % highest_profit_crypto_id).json()
    lowest_profit_data = get('https://api.coingecko.com/api/v3/coins/%s' % lowest_profit_crypto_id).json()
    highest_profit_graphdata = get(
        'https://api.coingecko.com/api/v3/coins/%s/market_chart?vs_currency=usd&days=1&interval=hourly' % highest_profit_crypto_id).json()

    lowest_profit_graphdata = get(
        'https://api.coingecko.com/api/v3/coins/%s/market_chart?vs_currency=usd&days=1&interval=hourly' % lowest_profit_crypto_id).json()

    prices_highest_profit, dates_highest_profit, dates_day1_highest_profit = getgraphdata(1, highest_profit_crypto_id, all_crypto, highest_profit_graphdata)
    prices_lowest_profit, dates_lowest_profit, dates_day1_lowest_profit = getgraphdata(1, lowest_profit_crypto_id, all_crypto, lowest_profit_graphdata)
    fig = Figure()
    fig.add_trace(Scatter(arg=dict(x=dates_highest_profit, y=prices_highest_profit,
                                   mode='markers+lines', name='crypto',
                                   opacity=0.8, marker_color='blue')))

    fig.update_layout(xaxis_title="Dates", yaxis_title="Value")
    plot_div_highest_profit = plot(fig, output_type='div')
    fig2 = Figure()
    fig2.add_trace(Scatter(arg=dict(x=dates_lowest_profit, y=prices_lowest_profit,
                                    mode='markers+lines', name='crypto',
                                    opacity=0.8, marker_color='red')))
    fig2.update_layout(xaxis_title="Dates", yaxis_title="Value", )
    plot_div_lowest_profit = plot(fig2, output_type='div')
    return render(request, 'CryptoPeek/home.html',
                  {'all_crypto': all_crypto, 'highest_profit_data': highest_profit_data, 'lowest_profit_data': lowest_profit_data,
                   'plot_div_highest_profit': plot_div_highest_profit, 'plot_div_lowest_profit': plot_div_lowest_profit})


def currencies(request):
    all_crypto = get(
        'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&sparkline=false').json()
    if request.method == 'POST':
        form = CryptoListForm(request.POST)
        if 'action' in request.POST:
            action = request.POST['action']
        else:
            action = False

        if action == 'Log out':
            logout(request)
        elif action == 'Search':
            all_crypto = get(
                'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&sparkline=false').json()

            if form.is_valid():
                name = form.cleaned_data['name']
                from_price = form.cleaned_data['from_price']
                to_price = form.cleaned_data['to_price']
                sort_type = form.cleaned_data['sort']
                input_dict = all_crypto
                input_dict = filter_data(name,input_dict,from_price,to_price,sort_type)
                return render(request, 'CryptoPeek/currencies.html', {'all_crypto': input_dict, 'form': form})

    else:
        form = CryptoListForm()
    return render(request, 'CryptoPeek/currencies.html', {'all_crypto': all_crypto, "form": form})


def detail(request, crypto_id):
    all_crypto = get(
        'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&sparkline=false').json()
    curr_crypto = get('https://api.coingecko.com/api/v3/coins/%s' % crypto_id).json()
    day = 1
    week = 7
    month = 31
    year = 365

    day_data = get(
        'https://api.coingecko.com/api/v3/coins/%s/market_chart?vs_currency=usd&days=%d&interval=hourly' % (
            crypto_id, day)).json()
    week_data = get(
        'https://api.coingecko.com/api/v3/coins/%s/market_chart?vs_currency=usd&days=%d&interval=daily' % (
            crypto_id, week)).json()
    month_data = get(
        'https://api.coingecko.com/api/v3/coins/%s/market_chart?vs_currency=usd&days=%d&interval=daily' % (
            crypto_id, month)).json()
    year_data = get(
        'https://api.coingecko.com/api/v3/coins/%s/market_chart?vs_currency=usd&days=%d&interval=daily' % (
            crypto_id, year)).json()
    day_prices, dates_day, day_day1 = getgraphdata(day, crypto_id, all_crypto, day_data)
    week_prices, dates_week, week_day1 = getgraphdata(week, crypto_id, all_crypto, week_data)
    month_prices, dates_month, month_day1 = getgraphdata(month, crypto_id, all_crypto, month_data)
    year_prices, dates_year, year_day1 = getgraphdata(year, crypto_id, all_crypto, year_data)
    fig = Figure()
    fig.add_trace(Scatter(arg=dict(visible=True, name='Day', x=dates_day, y=day_prices, mode='markers+lines', opacity=0.8,
                                   marker_color='blue')))
    fig.add_trace(Scatter(arg=dict(visible=False, name='Week', x=dates_week, y=week_prices, mode='markers+lines', opacity=0.8,
                                   marker_color='orange')))
    fig.add_trace(Scatter(arg=dict(visible=False, name='Month', x=dates_month, y=month_prices, mode='markers+lines', opacity=0.8,
                                   marker_color='green')))
    fig.add_trace(Scatter(arg=dict(visible=False, name='Year', x=dates_year, y=year_prices, mode='markers+lines', opacity=0.8,
                                   marker_color='purple')))
    fig.update_layout(xaxis_title="Dates", yaxis_title="Value", title=datetime.datetime.now().strftime("%m/%d/%y"),
                      updatemenus=[layout.Updatemenu(
                          active=0,
                          buttons=
                          [
                              dict(label='Day',
                                   method='update',
                                   args=[{'visible': [True, False, False, False]},
                                         {'title': datetime.datetime.now().strftime("%m/%d/%y")}]),
                              dict(label='Week',
                                   method='update',
                                   args=[{'visible': [False, True, False, False]}, {'title': week_day1.strftime(
                                       "%m/%d/%y") + ' - ' + datetime.datetime.now().strftime("%m/%d/%y")}]),
                              dict(label='Month',
                                   method='update',
                                   args=[{'visible': [False, False, True, False]}, {'title': month_day1.strftime(
                                       "%m/%d/%y") + ' - ' + datetime.datetime.now().strftime("%m/%d/%y")}]),
                              dict(label='Year',
                                   method='update',
                                   args=[{'visible': [False, False, False, True]}, {'title': year_day1.strftime(
                                       "%m/%d/%y") + ' - ' + datetime.datetime.now().strftime("%m/%d/%y")}]),
                          ]
                      )
                      ]
                      )

    plot_div = plot(fig, output_type='div')
    liked_status = 0
    if request.user.is_authenticated:
        this_users_fav = user_favourites.find_one({'username': request.user.username})['favourites']
        if crypto_id in this_users_fav:
            liked_status = 1
        if request.method == 'POST':
            if 'action' in request.POST:
                action = request.POST['action']
            else:
                action = False
            if 'like' in request.POST:
                like = request.POST['like']
            else:
                like = False
            if like == '🤍':
                user_favourites.update_one({'username': request.user.username}, {"$push": {'favourites': crypto_id}})
                liked_status = 1
            if like == "❤️":
                user_favourites.update_one({'username': request.user.username}, {"$pull": {'favourites': crypto_id}})
                liked_status = 0
            if action == 'Log out':
                logout(request)
                return render(request, 'CryptoPeek/details.html',
                              {'curr_crypto': curr_crypto, 'plot_div': plot_div, 'all_crypto': all_crypto, "liked_status": 0})
    else:
        if request.method == 'POST':
            return redirect('/cryptopeek/login/')
    return render(request, 'CryptoPeek/details.html',
                  {'curr_crypto': curr_crypto, 'plot_div': plot_div, 'all_crypto': all_crypto, "liked_status": liked_status})
