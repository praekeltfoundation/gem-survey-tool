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
                filters: [{loperator: null, operator: null, value: null}]
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

    $scope.processQueryResults = function processQueryResults(results, _columns){

        var columns = _columns.slice();
        var rows = [];

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

        for(var x = foundData.length - 1; x > -1; --x){
            if(foundData[x] === false){
                columns.splice(x, 1);
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

        return [columns, rows];
    };

    $scope.fetchStats();
});
