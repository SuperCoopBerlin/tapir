const search = document.getElementById('search-input')
search.addEventListener('input', (event) => {

    params = Tapir.getUrlParams()
    params.q = event.target.value.toLowerCase()
    Tapir.replaceUrlParams(params)

    handleSearch(params.q)
})

const handleSearch = (query) => {
    for(const param of document.getElementsByClassName('single-parameter')){
        if(!param.innerHTML.toLowerCase().includes(query)){
            param.style.display = 'none'
        } else {
            param.style.display = 'block'
        }
    }

    for(const category of document.getElementsByClassName('parameter-category')){
        if(Array.from(category.getElementsByClassName('single-parameter')).filter(it => it.style.display != 'none').length === 0){
            category.style.display = 'none'
        } else {
            category.style.display = 'block'
        }
    }
}

const init = () => {
    // apply search query from url
    const params = Tapir.getUrlParams()
    if(params.q){
        const query = decodeURIComponent(params.q)
        search.getElementsByClassName('form-control')[0].value = query
        handleSearch(query)
    }

    // scroll to the first field with an error
    for(elem of document.getElementsByClassName('single-parameter')){
            if(elem.getElementsByClassName('is-invalid').length > 0){
                elem.scrollIntoView()
            }
    }
}
init()