async function getOneStoreItems(sort, limit = 100, offset = 0) {
    tableBody.empty()
    const response = await axios.get(`/api/one?sort=${sort}&reverse=${reversed}&limit=${limit}&offset=${offset}`)
    const ranks = _.sortedUniqBy(response.data.items, ({market_appid}) => market_appid)
    _.forEach(ranks, ranking => {
        const {market_appid, icon_url, app_name, downloads, volume, genre, released} = ranking
        const template = `<tr data-bs-toggle="modal"
                data-bs-target="#staticBackdrop"
                onclick="showHistory('${market_appid}')">
                <td class="center one-${market_appid}">
                ${market_appid}</td>
                <td class="left"><span class="app-name">
                <img alt="app-icon" width="38" height="38" class="app-icon false" src="${icon_url}"><span>
                <span>${app_name}</span></span></span></td>
                <td class="center">${downloads}</td>
                <td class="center">${genre}</td>
                <td class="center">${volume}</td>
                <td class="center">${released}</td></tr>`
        tableBody.append(template)
    })
}

const showHistory = (appId) => {
    axios.get(`/api/one/${appId}?sort=${sortingKey}&reverse=${reversed}&limit=100&offset=0`)
        .then(res => res.data.items)
        .then(items => {
            let downs = _.map(items, "downloads")
            let dates = _.map(items, "created_at")
            _.forEach(_.zip(downs, dates), function ([down, date]) {
                console.log(down)
                console.log(moment(date).fromNow())
            })
        })
}
const getMyRanks = () => {
    axios.get(`/api/following?sort=created_at&reverse=true&limit=100&offset=0`)
        .then(res => res.data.items)
        .then((items) => {
            let item_array = _.groupBy(items, ({
                                                   app_name,
                                                   deal_type,
                                                   market,
                                                   rank_type
                                               }) => _.join([app_name, deal_type, market, rank_type], " "))
            _.forEach(item_array, (item, name) => {
                console.log(name)
                console.log(item)
                let names = _.map(item, "app_name")
                let ranks = _.map(item, "rank")
                console.log(names.shift(), ranks)
            })
        })
}
const some = (index, response) => {
    let {market, icon_url, app_name, date, rank_type, deal_type, rank} = response
    let template = `<tr>
            <td class="center">${index + 1}</td>
            <td class="center">
            <img alt="app-icon" class="app-icon" width="38" height="38" src="${icon_url}">
            </td><td class="left">
            <span class="app-name">${app_name}</span>
            </td><td><span>${date}</span>
            </td><td class="center">
            <div class="markets">
            [[[[__market__]]]]
            </div></td><td class="center">${rank_type}</td>
            <td class="center">${deal_type}</td>
            <td class="center">${rank}</td>
        </tr>`
    if (market === "google") {
        template.replace('[[[[__market__]]]]',
            `<p class="google"><svg xmlns="http://www.w3.org/2000/svg" width="38" height="38" fill="none" viewBox="0 0 38 38" version="1.1">
                    <g id="g1506" transform="matrix(2,0,0,1.8181818,-19,-15.545454)">
                        <path id="path943" d="m 9.5,9.993 v 18.014 c 0,0.663 0.3,1.144 0.902,1.443 L 20.93,19 10.402,8.55 C 9.801,8.815 9.5,9.296 9.5,9.993 Z" fill="#46cdfd"></path>
                        <path id="path945" d="m 28.5,19 c 0,-0.498 -0.218,-0.912 -0.652,-1.244 L 25.442,16.363 22.733,19 25.44,21.637 27.897,20.244 C 28.298,19.912 28.499,19.497 28.499,19 Z" fill="#fed330"></path>
                        <path id="path947" d="m 12.759,28.903 11.53,-6.569 -2.456,-2.438 z" fill="#fc363b"></path>
                        <path id="path949" d="m 24.29,15.666 -11.532,-6.569 9.074,9.007 2.456,-2.438 z" fill="#53fd55"></path>
                    </g>
                </svg></p>`)
    } else if (market === "apple") {
        template.replace("[[[[__market__]]]]",
            `<p class="apple">
                    <svg xmlns="http://www.w3.org/2000/svg" width="38" height="38" fill="none" viewBox="0 0 38 38">
                        <path fill-rule="evenodd" d="M 3.4381362,0 C 1.538566,0 0,1.538566 0,3.4381362 V 34.561864 C 0,36.461434 1.538566,38 3.4381362,38 H 34.561864 C 36.459716,38 38,36.461434 38,34.561864 V 3.4381362 C 38,1.538566 36.459716,0 34.561864,0 Z m 14.9352648,7.9111514 0.766703,1.3099298 0.751234,-1.3099298 c 0.481338,-0.8182764 1.524813,-1.0950464 2.351683,-0.6274599 0.825154,0.4761819 1.105362,1.51278 0.632618,2.3310563 l -1.753449,3.0152462 5.616195,9.638814 h 4.383623 c 0.952366,0 1.719069,0.759828 1.719069,1.701878 0,0.945487 -0.766703,1.705315 -1.719069,1.705315 H 15.480209 c -0.749514,-1.394164 0.22004,-3.407193 1.949422,-3.407193 h 5.335988 L 15.387378,9.6147478 C 14.916355,8.7964715 15.194843,7.7512781 16.019995,7.2836915 16.846868,6.816105 17.900657,7.092875 18.373401,7.9111514 Z m 9.05605,22.3581996 -1.653744,-2.8399 c 0.893916,-1.067542 2.025063,-1.394165 3.407193,-0.967836 l 1.230853,2.10414 c 0.472744,0.818276 0.194255,1.863469 -0.632618,2.331056 -0.825152,0.467587 -1.880659,0.192536 -2.351684,-0.62746 z M 7.0567745,22.275685 h 4.4764535 l 0.453834,-0.780458 c 2.025062,-3.477675 3.561909,-6.116444 4.613979,-7.904274 1.019408,0.833747 2.049129,3.307487 0.606831,5.770911 l -2.465144,4.228907 -3.89197,6.67858 C 10.369419,31.089347 9.3242254,31.364398 8.4973535,30.896811 7.6722009,30.420629 7.3937119,29.384031 7.8647366,28.565755 L 9.5425471,25.684596 H 7.0567745 c -0.9523637,0 -1.719068,-0.759827 -1.719068,-1.703596 0,-0.945488 0.7667043,-1.703597 1.719068,-1.703597 z" clip-rule="evenodd" fill="#1bb1f8" stroke-width="1.71906805">
                        </path>
                </svg></p>`)
    } else if (market === "one") {
        template.replace("[[[[__market__]]]]",
            `<p class="one">
                    <svg xmlns="http://www.w3.org/2000/svg" width="38" height="38" fill="#FF3968" viewBox="0 0 38 38">
                        <path d="M 3.438136,0 C 1.5385659,0 0,1.5385659 0,3.4381362 V 34.561864 C 0,36.461434 1.5385659,38 3.438136,38 H 34.561864 C 36.459715,38 38,36.461434 38,34.561864 V 3.4381362 C 38,1.5385659 36.459715,0 34.561864,0 Z m 14.283737,14.216693 -3.41235,1.968333 c -1.330559,0.770142 -3.034155,0.31287 -3.802579,-1.019407 -0.770142,-1.330559 -0.31287,-3.034156 1.019408,-3.802579 l 7.369644,-4.2564125 c 0.455553,-0.3231848 1.010812,-0.5122823 1.610767,-0.5122823 0.416015,0 0.8114,0.091111 1.167247,0.2561411 0.510564,0.2303551 0.955802,0.6188645 1.258358,1.1414612 0.302556,0.5260349 0.416015,1.1087989 0.359285,1.6692151 V 28.619045 c 0,1.538566 -1.248043,2.784891 -2.78489,2.784891 -1.538566,0 -2.78489,-1.246325 -2.78489,-2.784891 V 15.177652 l 2.705813,-2.845058 -2.705813,1.887537 z" id="path863">
                        </path>
                </svg></p>`)
    }
}

function search() {
    let query = $("#search-input").val()
    let tableBody = $("#search-table-body")
    tableBody.empty()
    axios.post(`/api/ranking?query=${query}`)
        .then((res) => res.data)
        .then((data) => data.items.forEach((item) => {
            let {id, app_name, icon_url, package_name} = item
            let one = parseInt(package_name)
                ? `https://m.onestore.co.kr/mobilepoc/apps/appsDetail.omp?prodId=${package_name}`
                : `https://play.google.com/store/apps/details?id=${package_name}`
            let template = `<tr>
                        <td class="center">${id}</td>
                        <td class="center"><img src="${icon_url}" width="36" height="36" alt="${app_name}"></td>
                        <td class="left"><a href="${one}">${app_name}</a></td>
                        <td class="left">${package_name}</td>
                        <td class="center">
                            <button onclick="track('${app_name}')"
                            >추적</button>
                        </td>
                    </tr>`
            tableBody.append(template)
        }))
}

function track(appName) {
    axios.post(`http://127.0.0.1:8000/api/follow?app_name=${appName}`)
        .then((res) => res.data)
        .then((data) => {
            console.log(data)
        })
}

function onLoad() {
    let arr = window.location.pathname.split("/")
    game = arr.pop()
    deal = arr.pop()
    market = arr.pop()
}

function getData(market, ranking) {
    return axios.get(`/api/ranking?store=${market}&rtype=${ranking}&deal=${deal}&game=${game}&sort=created_at&reverse=true`)
        .then((res) => res.data)
        .then((data) => data.items)
}

const getResults = async () => {
    let free = await getData(market, "free")
    let paid = await getData(market, "paid")
    let gross = await getData(market, "gross")
    free = _.uniqBy(free, (app) => app["rank"])
    paid = _.uniqBy(paid, (app) => app["rank"])
    gross = _.uniqBy(gross, (app) => app["rank"])
    const item_array = _.groupBy([...free, ...paid, ...gross], 'rank')
    _.forEach(item_array, (items, rank) => {
        let template = `<tr><td class="center">${rank}</td>`
        _.forEach(items, (item) => {
            let {id, app_name, icon_url, package_name, market} = item
            let one = "#"
            if (market === "one") one = `https://m.onestore.co.kr/mobilepoc/apps/appsDetail.omp?prodId=${package_name}`
            if (market === "google") one = `https://play.google.com/store/apps/details?id=${package_name}`
            template += `<td class="left"><a class="app" target="_blank" href="${one}">
            <img alt="${app_name}" height="38" width="38" class="app-icon false" src="${icon_url}">
            <span class="text"><span title="${id} | ${app_name} | ${package_name} | ${rank}">${app_name}</span></span></a></td>`
        })
        template += `</tr>`
        $("tbody#statistic-table-body").append(template)
    })
}
