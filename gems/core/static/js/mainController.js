var gems = angular.module('gems');

gems.controller('mainController', function($scope, $http, $window){
    $scope.userMenuItem = false;
    $scope.builderMenuItem = false;
    $scope.contactsMenuItem = false;
    $scope.serviceMenuItem = false;
    $scope.dataMenuItem = false;
    $scope.adminMenuItem = false;

    $scope.showSurveyDataMenu = false;
    $scope.showContactMenu = false;
    $scope.showCreateGroup = false;
    $scope.showContactGroups = false;
    $scope.showExportSurvey = false;
    $scope.showExportSurveyData = false;
    $scope.groupNameMain = '';
    $scope.topQueryWords = '';
    $scope.groupKey = '';
    $scope.queryValid = false;
    $scope.showLandingStats = true;
    $scope.stats = {};
    $scope.origColumns = [];
    $scope.fields = [];

    $scope.filters = [];
    $scope.createGroup = true;

    $scope.itemsPerPage = 10;

    $scope.addFilter = function addFilter(){
        $scope.filters.push(
            {
                loperator: "and",
                field:null,
                filters: [{loperator: null, operator: null, value: null, tooltip: {items: null, show: false}}]
            })
    };

    $scope.toggleSurveyDataMenu = function toggleSurveyDataMenu(){
        $scope.showSurveyDataMenu = !$scope.showSurveyDataMenu;

        if($scope.showSurveyDataMenu == true){
            $scope.updateStats(false);
            $scope.showContactMenu = false;
        } else {
            $scope.updateStats(true);
        }
    };

    $scope.toggleContactMenu = function toggleContactMenu(){
        $scope.showContactMenu = !$scope.showContactMenu;

        if($scope.showContactMenu == true){
            $scope.updateStats(false);
            $scope.showSurveyDataMenu = false;
        } else {
            $scope.updateStats(true);
        }
    };

    $scope.hideSubMenus = function hideSubMenus(url){
        $scope.showSurveyDataMenu = false;
        $scope.showContactMenu = false;
        $scope.showCreateGroup = false;
        $scope.showContactGroups = false;
        $scope.showExportSurvey = false;
        $scope.showExportSurveyData = false;

        if(typeof(url) != 'undefined'){
            $window.open(url, "_blank");
        } else {
            $scope.updateStats(true);
        }
    };

    $scope.showCreateContact = function showCreateContact(){
        $scope.showContactGroups = false;
        $scope.showCreateGroup = true;
        $scope.showExportSurvey = false;
        $scope.showExportSurveyData = false;
        $scope.createGroup = true;
        $scope.rows = [];
        $scope.setGroupName('');
        $scope.filters = [];
        $scope.addFilter();
        $scope.fetchFields();
    };

    $scope.hideCreateContact = function hideCreateContact(){
        $scope.showCreateGroup = false;
        $scope.filters = [];
    };

    $scope.showViewContactGroups = function showViewContactGroups(){
        $scope.showContactGroups = true;
        $scope.showCreateGroup = false;
        $scope.showExportSurvey = false;
        $scope.showExportSurveyData = false;
    };

    $scope.hideViewContactGroups = function hideViewContactGroups(){
        $scope.showContactGroups = false;
    };

    $scope.showEditContact = function showEditContact(name, filters, group_key){
        $scope.showContactGroups = false;
        $scope.showCreateGroup = true;
        $scope.createGroup = false;
        if(typeof(filters) === 'string'){
            $scope.filters = JSON.parse(filters);
        } else {
            $scope.filters = filters;
        }
        $scope.setGroupName(name);
        $scope.groupKey = group_key;
    };

    $scope.showViewExportSurvey = function showViewExportSurvey(){
        $scope.showContactGroups = false;
        $scope.showCreateGroup = false;
        $scope.showExportSurvey = true;
        $scope.showExportSurveyData = false;
    };

    $scope.hideViewExportSurvey = function hideViewExportSurvey(){
        $scope.showExportSurvey = false;
    };

    $scope.showViewExportSurveyData = function showViewExportSurveyData(){
        $scope.showContactGroups = false;
        $scope.showCreateGroup = false;
        $scope.showExportSurvey = false;
        $scope.showExportSurveyData = true;
        $scope.filters = [];
        $scope.addFilter();
    };

    $scope.hideViewExportSurveyData = function hideViewExportSurveyData(){
        $scope.showExportSurveyData = false;
        $scope.filters = [];
    };

    $scope.hideViews = function hideViews(){
        $scope.showContactGroups = false;
        $scope.showCreateGroup = false;
        $scope.showExportSurvey = false;
        $scope.showExportSurveyData = false;
    };

    $scope.getGroupName = function getGroupName(){
        return $scope.groupNameMain;
    };

    $scope.setGroupName = function setGroupName(name){
        $scope.groupNameMain = name;
    };

    $scope.setQueryWords = function setQueryWords(qw){
        $scope.topQueryWords = qw;
    };

    $scope.getQueryWords = function getQueryWords(){
        return $scope.topQueryWords;
    };

    $scope.unboldMenuItems = function unboldMenuItems()
    {
        $scope.userMenuItem = false;
        $scope.builderMenuItem = false;
        $scope.contactsMenuItem = false;
        $scope.serviceMenuItem = false;
        $scope.dataMenuItem = false;
        $scope.adminMenuItem = false;
    }

    $scope.setQueryValid = function setQueryValid(valid){
        $scope.queryValid = valid;
    }

    $scope.getQueryValid = function getQueryValid(){
        return $scope.queryValid;
    }

    $scope.formatDate = function formatDate(value){
        if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}\w/.test(value))
        {
            return value.substr(0, 10);
        }
        else
        {
            return value;
        }
    };

    $scope.groupToPages = function(results){
        var paged = [];
        var temp = results.slice();
        while (temp.length > 0)
        {
            paged.push(temp.splice(0, $scope.itemsPerPage));
        }
        return paged;
    };

    $scope.range = function (start, end){
        var ret = [];
        if (!end){
            end = start;
            start = 0;
        }
        for (var i = start; i < end; i++){
            ret.push(i);
        }
        return ret;
    };

    $scope.updateStats = function updateStats(value){
        $scope.showLandingStats = value;

        if($scope.showLandingStats){
            $scope.fetchStats();
        }
    }

    $scope.fetchStats = function fetchStats(){
        $http.get("/get_stats/")
            .success(function(data){
                $scope.stats = data;
            });
    };

    $scope.fetchFields = function fetchFields(){
        $http.get('/get_unique_keys/')
            .success(function(data){
                $scope.fields = data;
                $scope.origColumns = $scope.fields.slice();
            })
    };

    $scope.processQueryResults = function processQueryResults(results, _columns, _filters){

        var columns = _columns.slice();
        var filters = _filters.slice();
        var rows = [];

        // prep the columns with hide
        // first 4: can't be hidden
        // last n: can be hidden unless in the filter
        for(var x = 0; x < columns.length; ++x){
            if(x > 3){
                columns[x].noHide = false;
                columns[x].hide = true;
            }
            else{
                columns[x].noHide = true;
                columns[x].hide = false;
            }
        }

        // Construct the fields
        for(var x = 0; x < results.length; ++x){
            var fields = results[x].fields;
            var answer = fields['answer'];
            var row = {
                selected: false,
                fields: []
            };

            fields.id = results[x].pk;

            for(var y = 0; y < columns.length; ++y){
                var column = columns[y];

                if(fields.hasOwnProperty(column.name)){
                    row.fields.push(fields[column.name]);
                } else if(answer.hasOwnProperty(column.name)){
                    row.fields.push(answer[column.name]);
                } else {
                    row.fields.push('');
                }
            }

            rows.push(row);
        }

        // Establish what columns need to be removed
        var foundData = new Array();

        for(var x = 0; x < columns.length; ++x){
            foundData.push(false);
        }

        for(var x = 0; x < rows.length; ++x){
            for(var y = 0; y < columns.length; ++y){
                if(foundData[y] === false && rows[x].fields[y] !== ''){
                    foundData[y] = true;
                }
            }
        }

        // Remove those columns
        for(var x = foundData.length - 1; x > -1; --x){
            if(foundData[x] === false){
                columns.splice(x, 1);
            }
        }

        // Find columns that should not be hidden
        for(var x = 0; x < filters.length; ++x){
            var name = filters[x].field.name;
            for(var x = 4; x < columns.length; ++x){
                if(columns[x].name === name){
                    columns[x].hide = false;
                    columns[x].noHide = true;
                }
            }
        }

        // Construct the fields based on the removed columns
        rows = [];

        for(var x = 0; x < results.length; ++x){
            var fields = results[x].fields;
            var answer = fields['answer'];
            var row = {
                selected: false,
                fields: []
            };

            fields.id = results[x].pk;

            for(var y = 0; y < columns.length; ++y){
                var column = columns[y];
                var val = null;

                if(fields.hasOwnProperty(column.name)){
                    val = fields[column.name];
                } else if(answer.hasOwnProperty(column.name)){
                    val = answer[column.name];
                }

                row.fields.push(
                    {
                        value: val,
                        hide: column.hide,
                        noHide: column.noHide
                    });
            }

            rows.push(row);
        }

        return [columns, rows];
    };

    $scope.showAlert = function(type, heading, message) {
        var html =
            '<div class="alert ' + type + '">' +
                '<a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a>' +
                '<strong>' + heading + '! </strong> ' + message +
            '</div>';

        $('.alerts-container').append(html);
        $scope.alertTimeout(5000);
    }

    $scope.alertTimeout = function(wait){
        setTimeout(function() {
            $('.alerts-container').children('.alert:first-child').fadeOut(300, function() { $(this).remove()});
        }, wait);
    }

    $scope.toggleColumnsAndRows = function toggleColumnsAndFields(_columns, _rows){
        var columns = _columns.slice();
        var rows = _rows.slice();

        for(var x = 0; x < columns.length; ++x){
            if(!columns[x].noHide){
                columns[x].hide = !columns[x].hide;
            }
        }

        for(var x = 0; x < rows.length; ++x){
            for(var y = 0; y < rows[x].fields.length; ++y){
                if(!rows[x].fields[y].noHide){
                    rows[x].fields[y].hide = !rows[x].fields[y].hide;
                }
            }
        }

        return [columns, rows];
    }

    $scope.fetchStats();
});
