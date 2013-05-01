(function ($) {

    var SearchResult = Backbone.Model.extend({
        defaults:{
            term:'none',
            count:0,
            url:'none',
            wiki_image:'none',
            wiki_text:'none',
            text_loc: [0,0],
            text_before: 'none',
            text_after: 'none',
            flickr_urls: []
        }
    });

    var SearchResults = Backbone.Collection.extend({
        model:SearchResult,
        url:'/search/',

        parse: function(response){
            response = response.results;
            console.log(response);
            return response;
      }

    });

    var SearchResultView = Backbone.View.extend({
        tagName:"div",
        className:"searchResult",
        template:$("#searchResultTemplate").html(),

        render:function() {
            var tmpl = _.template(this.template);
            this.$el.html(tmpl(this.model.toJSON()));
            return this;
        }
    });

    var SearchResultsView = Backbone.View.extend({
        el:$("#search"),

        events:{
            'click #search_button': 'search'
        },

        render:function(){
            var that = this;
            _.each(this.collection.models, function(item){
                that.renderSearchResult(item);
            }, this);
        },

        renderSearchResult:function(item){
            var searchResultView = new SearchResultView({
                model:item
            });
            this.$el.append(searchResultView.render().el);
        },

        search:function(){
            $('.searchResult').remove();
            this.collection = new SearchResults();
            this.collection.bind('reset', this.render, this);
            this.collection.bind('reset', this.insertResultsLinks, this);
            this.collection.fetch( {data: { 'text': $('#search_input').val() }, type: 'POST' });
            this.updatePageQuery();
            this.render();
        },

        updatePageQuery:function(){
            var query = $('#search_input').val();
            $('#searchQuery').html('<h5 id="queryText">'+query+'</h5>');
        },

        insertResultsLinks:function(){
            var queryText = $('#search_input').val();
            console.log(queryText);
            _.each(this.collection.models, function(model){
                $('#searchQuery').highlight(model.get('term'),model.get('url'));
                //queryText.replace(model.get('term'),"abcd");
                //$('queryText').contents().replace(model.get('term'), "<a class='marked' href="+model.get('url')+">"+model.get('term')+"</a>");

                //console.log(model.get('text_before'));
                //console.log(queryString.find(model.get('text_before')));
                //console.log(model.get('text_after'));
                //console.log(model.get('offset'));
            });
            console.log(queryText);
        }

    });

    var searchResultsView = new SearchResultsView();

})(jQuery);
