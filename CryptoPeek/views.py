import datetime
import math
from django.contrib.auth import login, authenticate, logout
from plotly.offline import plot
from plotly.graph_objs import Scatter, Figure, layout, Bar
from django.shortcuts import render, redirect
from requests import get
import pymongo
from .forms import CryptoListForm, SignUpForm, SignInForm, CompareForm

connection_string = 'mongodb+srv://dgrzesik:cryptopeekdgrzesik@cluster0.r6kad.mongodb.net/CryptoPeek?retryWrites=true&w=majority'
my_client = pymongo.MongoClient(connection_string)
dbname = my_client['CryptoPeek']
all_favourites = dbname['User_Favourites']


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
                all_favourites.insert_one({"username": user.username, "favourites": []})
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
    all_favourites.update_one({'username': request.user.username}, {"$pull": {'favourites': crypto_id}})
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
            allcrypto = get(
                'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&sparkline=false').json()
            if crypto1 and crypto2:
                crypto1_overall = [x for x in allcrypto if crypto1.lower() in x['name'].lower()]
                crypto2_overall = [x for x in allcrypto if crypto2.lower() in x['name'].lower()]
                if crypto1_overall != [] and crypto2_overall != []:
                    crypto1_overall = crypto1_overall[0]
                    crypto2_overall = crypto2_overall[0]
                    yd1 = get(
                        'https://api.coingecko.com/api/v3/coins/%s/market_chart?vs_currency=usd&days=%d&interval=daily' % (
                            crypto1_overall["id"], 30)).json()
                    pricesy_1, datesy_1, day_1_y_1 = getgraphdata(30, crypto1, allcrypto, yd1)
                    yd2 = get(
                        'https://api.coingecko.com/api/v3/coins/%s/market_chart?vs_currency=usd&days=%d&interval=daily' % (
                            crypto2_overall["id"], 30)).json()
                    pricesy_2, datesy_2, day_1_y_2 = getgraphdata(30, crypto2, allcrypto, yd2)
                    fig = Figure()
                    fig.add_trace(
                        Scatter(arg=dict(visible=True, name=crypto1_overall['name'], x=datesy_1, y=pricesy_1,
                                         mode='markers+lines', opacity=0.8,
                                         marker_color='blue')))
                    fig.add_trace(
                        Scatter(
                            arg=dict(visible=True, name=crypto2_overall['name'], x=datesy_2, y=pricesy_2,
                                     mode='markers+lines', opacity=0.8,
                                     marker_color='red')))
                    fig.update_layout(xaxis_title="Dates", yaxis_title="Value", width=1000, height=600)

                    plot_div = plot(fig, output_type='div')
                    return render(request, 'CryptoPeek/compare.html',
                                  {"currency1": crypto1_overall, "currency2": crypto2_overall, "plot_div": plot_div,
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
        apidata = get(
            'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&sparkline=false').json()
        this_users_fav = all_favourites.find_one({'username': request.user.username})['favourites']
        apidata = [x for x in apidata if x['id'] in this_users_fav]
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
                apidata = get(
                    'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&sparkline=false').json()
                if form.is_valid():
                    name = form.cleaned_data['name']
                    from_price = form.cleaned_data['from_price']
                    to_price = form.cleaned_data['to_price']
                    sort_type = form.cleaned_data['sort']
                    this_users_fav = all_favourites.find_one({'username': request.user.username})['favourites']
                    apidata = [x for x in apidata if x['id'] in this_users_fav]
                    input_dict = apidata
                    if from_price:
                        input_dict = [x for x in input_dict if x['current_price'] <= to_price]
                    if to_price:
                        input_dict = [x for x in input_dict if from_price <= x['current_price']]
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

                    return render(request, 'CryptoPeek/favourite.html', {'apidata': input_dict, 'form': form})

        else:
            form = CryptoListForm()
        return render(request, 'CryptoPeek/favourite.html', {'apidata': apidata, "form": form})
    else:
        return redirect('/cryptopeek/favourite/login/')


def home(request):
    if request.method == 'POST':
        if request.POST['action'] == 'Log out':
            logout(request)
            return redirect('/cryptopeek/home/')
    apidata = get(
        'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&sparkline=false').json()
    highest_profit = -math.inf
    lowest_profit = math.inf
    h_p_id = ""
    l_p_id = ""
    for crypto in apidata:
        if crypto["price_change_percentage_24h"] > highest_profit:
            highest_profit = crypto["price_change_percentage_24h"]
            h_p_id = crypto["id"]
        if crypto["price_change_percentage_24h"] < lowest_profit:
            lowest_profit = crypto["price_change_percentage_24h"]
            l_p_id = crypto["id"]
    highest_data = get('https://api.coingecko.com/api/v3/coins/%s' % h_p_id).json()
    lowest_data = get('https://api.coingecko.com/api/v3/coins/%s' % l_p_id).json()
    graphdata = get(
        'https://api.coingecko.com/api/v3/coins/%s/market_chart?vs_currency=usd&days=1&interval=hourly' % h_p_id).json()

    graphdata2 = get(
        'https://api.coingecko.com/api/v3/coins/%s/market_chart?vs_currency=usd&days=1&interval=hourly' % l_p_id).json()

    pricesh, datesh, begin_h = getgraphdata(1, h_p_id, apidata, graphdata)
    pricesl, datesl, begin_l = getgraphdata(1, l_p_id, apidata, graphdata2)
    fig = Figure()
    fig.add_trace(Scatter(arg=dict(x=datesh, y=pricesh,
                                   mode='markers+lines', name='crypto',
                                   opacity=0.8, marker_color='blue')))

    fig.update_layout(xaxis_title="Dates", yaxis_title="Value")
    plot_div_h = plot(fig, output_type='div')
    fig2 = Figure()
    fig2.add_trace(Scatter(arg=dict(x=datesl, y=pricesl,
                                    mode='markers+lines', name='crypto',
                                    opacity=0.8, marker_color='red')))
    fig2.update_layout(xaxis_title="Dates", yaxis_title="Value", )
    plot_div_l = plot(fig2, output_type='div')
    return render(request, 'CryptoPeek/home.html',
                  {'apidata': apidata, 'highest_data': highest_data, 'lowest_data': lowest_data,
                   'plot_div_h': plot_div_h, 'plot_div_l': plot_div_l})


def index(request):
    apidata = get(
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
            apidata = get(
                'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&sparkline=false').json()

            if form.is_valid():
                name = form.cleaned_data['name']
                from_price = form.cleaned_data['from_price']
                to_price = form.cleaned_data['to_price']
                sort_type = form.cleaned_data['sort']
                input_dict = apidata
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

                return render(request, 'CryptoPeek/currencies.html', {'apidata': input_dict, 'form': form})

    else:
        form = CryptoListForm()
    return render(request, 'CryptoPeek/currencies.html', {'apidata': apidata, "form": form})


def getgraphdata(days, crypto_id, apidataall, graphdata):
    prices = []
    dates = []
    curr_date = datetime.datetime.now() - datetime.timedelta(days)
    first_date = curr_date
    for crypto in apidataall:
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


def detail(request, crypto_id):
    apidataall = get(
        'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&sparkline=false').json()
    apidata = get('https://api.coingecko.com/api/v3/coins/%s' % crypto_id).json()
    daysd = 1
    daysw = 7
    daysm = 31
    daysy = 365

    dd = get(
        'https://api.coingecko.com/api/v3/coins/%s/market_chart?vs_currency=usd&days=%d&interval=hourly' % (
            crypto_id, daysd)).json()
    wd = get(
        'https://api.coingecko.com/api/v3/coins/%s/market_chart?vs_currency=usd&days=%d&interval=daily' % (
            crypto_id, daysw)).json()
    md = get(
        'https://api.coingecko.com/api/v3/coins/%s/market_chart?vs_currency=usd&days=%d&interval=daily' % (
            crypto_id, daysm)).json()
    yd = get(
        'https://api.coingecko.com/api/v3/coins/%s/market_chart?vs_currency=usd&days=%d&interval=daily' % (
            crypto_id, daysy)).json()
    pricesd, datesd, day_1_d = getgraphdata(daysd, crypto_id, apidataall, dd)
    pricesw, datesw, day_1_w = getgraphdata(daysw, crypto_id, apidataall, wd)
    pricesm, datesm, day_1_m = getgraphdata(daysm, crypto_id, apidataall, md)
    pricesy, datesy, day_1_y = getgraphdata(daysy, crypto_id, apidataall, yd)
    fig = Figure()
    fig.add_trace(Scatter(arg=dict(visible=True, name='Day', x=datesd, y=pricesd, mode='markers+lines', opacity=0.8,
                                   marker_color='blue')))
    fig.add_trace(Scatter(arg=dict(visible=False, name='Week', x=datesw, y=pricesw, mode='markers+lines', opacity=0.8,
                                   marker_color='orange')))
    fig.add_trace(Scatter(arg=dict(visible=False, name='Month', x=datesm, y=pricesm, mode='markers+lines', opacity=0.8,
                                   marker_color='green')))
    fig.add_trace(Scatter(arg=dict(visible=False, name='Year', x=datesy, y=pricesy, mode='markers+lines', opacity=0.8,
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
                                   args=[{'visible': [False, True, False, False]}, {'title': day_1_w.strftime(
                                       "%m/%d/%y") + ' - ' + datetime.datetime.now().strftime("%m/%d/%y")}]),
                              dict(label='Month',
                                   method='update',
                                   args=[{'visible': [False, False, True, False]}, {'title': day_1_m.strftime(
                                       "%m/%d/%y") + ' - ' + datetime.datetime.now().strftime("%m/%d/%y")}]),
                              dict(label='Year',
                                   method='update',
                                   args=[{'visible': [False, False, False, True]}, {'title': day_1_y.strftime(
                                       "%m/%d/%y") + ' - ' + datetime.datetime.now().strftime("%m/%d/%y")}]),
                          ]
                      )
                      ]
                      )

    plot_div = plot(fig, output_type='div')
    liked = 0
    if request.user.is_authenticated:
        this_users_fav = all_favourites.find_one({'username': request.user.username})['favourites']
        if crypto_id in this_users_fav:
            liked = 1
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
                all_favourites.update_one({'username': request.user.username}, {"$push": {'favourites': crypto_id}})
                liked = 1
            if like == "❤️":
                all_favourites.update_one({'username': request.user.username}, {"$pull": {'favourites': crypto_id}})
                liked = 0
            if action == 'Log out':
                logout(request)
                return render(request, 'CryptoPeek/details.html',
                              {'apidata': apidata, 'plot_div': plot_div, 'apidataall': apidataall, "liked": 0})
    else:
        if request.method == 'POST':
            return redirect('/cryptopeek/login/')
    return render(request, 'CryptoPeek/details.html',
                  {'apidata': apidata, 'plot_div': plot_div, 'apidataall': apidataall, "liked": liked})
