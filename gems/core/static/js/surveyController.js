var gems = angular.module('gems');

gems.controller('surveyController', function($scope, $http){
    $scope.Surveys = {};
    $scope.selected = {
        survey: null
    };
    $scope.queryStarted = false;
    $scope.surveySearchForm = {
        name : null,
        from : null,
        to : null
    };
    $scope.numberOfRows = 0;
    $scope.columns = [];
    $scope.rows = [];
    $scope.buttonText = "Display Results";
    $scope.queryDone = true;

    $scope.pagedGroups = [];
    $scope.currentPage = 1;
    $scope.showAllResults = false;
    $scope.dispCol = {
        hide: false
    };

    $scope.getSurveys = function getSurveys(){
        $scope.queryStarted = true;
        var payload = {};

        if (!!$scope.surveySearchForm.name)
        {
            payload.name = $scope.surveySearchForm.name;
        }

        if (!!$scope.surveySearchForm.from)
        {
            payload.from = $scope.surveySearchForm.from;
        }

        if (!!$scope.surveySearchForm.to)
        {
            payload.to = $scope.surveySearchForm.to;
        }

        $http({
                url: '/get_surveys/',
                method: 'POST',
                data: payload
            })
            .success(function(data){
                $scope.Surveys = data;
                results = data;
                $scope.rows = [];
                var row = {
                        selected: false,
                        fields: []
                    };

                for(var x = 0; x < results.length; ++x){
                    var row = {
                        selected: false,
                        pk: results[x].pk,
                        name: results[x].fields.name,
                        created_on: results[x].fields.created_on
                    };
                    $scope.rows.push(row);
                }
                $scope.currentPage = 0;
                $scope.pagedGroups = $scope.groupToPages($scope.rows);
            })
            .error(function(data){
                $scope.showAlert('alert-warning', 'Failed', 'Failed to retrieve the surveys');
            });
    };

    $scope.getAllSurveys = function getAllSurveys(){
        $http({
                url: '/get_surveys/',
                method: 'GET'
            })
            .success(function(data){
                $scope.AllSurveys = data;
            })
            .error(function(data){
                $scope.showAlert('alert-warning', 'Failed', 'Failed to retrieve the surveys');
            });
    }

    $scope.fetchResults = function fetchResults(){
        $scope.rows = [];
        $scope.queryStarted = true;
        $scope.queryDone = false;
        $scope.buttonText = "Loading Results";
        $scope.showAllResults = false;
        var payload = {};

        if($scope.numberOfRows != null && $scope.numberOfRows > 0){
            payload.limit = $scope.numberOfRows;
        }

        payload.filters = $scope.filters;
        $scope.columns = $scope.origColumns.slice();

        $http({
            url: '/query/',
            method: 'POST',
            data: payload
            })
            .then(function(data){
                var results = data.data;

                var retVal = $scope.processQueryResults(results, $scope.columns, payload.filters);
                $scope.columns = retVal[0];
                $scope.rows = retVal[1];

                $scope.currentPage = 0;
                $scope.pagedGroups = $scope.groupToPages($scope.rows);

                if ($scope.queryStarted == true){
                        $scope.buttonText = "Refresh Results";
                }else{
                    $scope.buttonText = "Display Results";
                }
                $scope.queryDone = true;
            })
    };

    $scope.selectRow = function selectRow(index){
        $scope.rows[index].selected = true;
    };

    $scope.selectFunction = function selectFunction(){
        if($scope.allRowsSelected()){
            // deselect all rows
            for(var x = 0; x < $scope.rows.length; ++x){
                $scope.rows[x].selected = false;
            }
        } else {
            // select all rows
            for(var x = 0; x < $scope.rows.length; ++x){
                $scope.rows[x].selected = true;
            }
        }
    };

    $scope.allRowsSelected = function allRowsSelected(){
        var retVal = true;

        for(var x = 0; x < $scope.rows.length; ++x){
            retVal = retVal && $scope.rows[x].selected;
        }

        return retVal;
    };

    $scope.anyRowsSelected = function anyRowsSelected(){
        var retVal = false;

        for(var x = 0; x < $scope.rows.length; ++x){
            retVal = retVal || $scope.rows[x].selected;
        }

        return retVal;
    };

    $scope.getSelectedRows = function getSelectedRows(){
        var rows = [];

        var idIndex = 0;

        for(var x = 0; x < $scope.fields.length; ++x){
            if($scope.fields[x].name === 'id' ){
                idIndex = x;
                break;
            }
        }

        for(var x = 0; x < $scope.rows.length; ++x){
            if($scope.rows[x].selected){
                rows.push($scope.rows[x].fields[idIndex]);
            }
        }

        return rows;
    };

    $scope.exportCsv = function exportCsv(){
        var data = $scope.getSelectedRows();

        var url = '/export_survey_results/?rows=[';

        for(var x = 0; x < data.length; ++x){
            if( x > 0){
                url += ',';
            }

            url += data[x].value;
        }

        url += ']';

        window.location.assign(url);
    };

    $scope.getSelectedSurveyRows = function getSelectedRows(){
        var rows = [];

        for(var x = 0; x < $scope.rows.length; ++x){
            if($scope.rows[x].selected){
                rows.push($scope.rows[x].pk);
            }
        }

        return rows;
    };

    $scope.exportSurveyCsv = function exportCsv(){
        var data = $scope.getSelectedSurveyRows();

        var url = '/export_survey/?pk=';

        for(var x = 0; x < data.length; ++x){
            var tempUrl = url + data[x];
            window.location.assign(tempUrl);
        }
    };

    $scope.exportSelectedSurvey = function() {
        var url = '/export_survey/?pk=' + $scope.selected.survey.pk;
        window.location.assign(url);
    }

    $scope.setPage = function (){
        $scope.currentPage = this.n;
    };

    $scope.initDTP = function initDTP(){
        var dtp_from = angular.element('#datepicker_from');
        var dtp_to = angular.element('#datepicker_to');

        if(dtp_from.length){
            dtp_from.datepicker({
                dateFormat: 'yy/mm/dd',
                maxDate: 0,
                onSelect:
                    function( selectedDate ) {
                        dtp_to.datepicker( "option", "minDate", selectedDate );
                        $scope.$apply($scope.surveySearchForm.from = selectedDate);
                    }
            });
        }

        if(dtp_to.length){
            dtp_to.datepicker({
                dateFormat: 'yy/mm/dd',
                maxDate: 0,
                onSelect:
                    function( selectedDate ) {
                        dtp_from.datepicker( "option", "maxDate", selectedDate );
                        $scope.$apply($scope.surveySearchForm.to = selectedDate);
                    }
            });
        }

        angular.element('.trigger_to').click(function() {
            angular.element('#datepicker_to').datepicker("show");
        });

        angular.element('.trigger_from').click(function() {
            angular.element('#datepicker_from').datepicker("show");
        });
    };

    $scope.queryValid = function queryValid(){
        return $scope.getQueryValid();
    };

    $scope.toggleShowAllResults = function toggleShowAllResults(){
        $scope.showAllResults = !$scope.showAllResults;

        var retVal = $scope.toggleColumnsAndRows($scope.columns, $scope.rows);
        $scope.columns = retVal[0];
        $scope.rows = retVal[1];
    };

    $scope.fetchFields();
    $scope.initDTP();
    $scope.getAllSurveys();
});