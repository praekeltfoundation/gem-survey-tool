var gems = angular.module('gems');

gems.controller('surveyController', function($scope, $http){
    $scope.Surveys = {};
    $scope.queryStarted = false;
    $scope.surveySearchForm = {
        name : null,
        from : null,
        to : null
    };
    $scope.numberOfRows = 0;
    $scope.columns = [];
    $scope.rows = [];

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
            })
            .error(function(data){
                alert("Failed to retreive the surveys");
            });
    };

    $scope.fetchResults = function fetchResults(){
        $scope.rows = [];
        $scope.queryStarted = true;
        var payload = {};

        if($scope.numberOfRows != null && $scope.numberOfRows > 0){
            payload.limit = $scope.numberOfRows;
        }

        payload.filters = $scope.filters;

        $http({
            url: '/query/',
            method: 'POST',
            data: payload
            })
            .then(function(data){
                var results = data.data;

                for(var x = 0; x < results.length; ++x){
                    var fields = results[x].fields;
                    var answer = fields['answer'];
                    var row = {
                        selected: false,
                        fields: []
                    };

                    fields.id = results[x].pk;

                    for(var y = 0; y < $scope.columns.length; ++y){
                        var column = $scope.columns[y];

                        if(fields.hasOwnProperty(column.name)){
                            row.fields.push(fields[column.name]);
                        } else if(answer.hasOwnProperty(column.name)){
                            row.fields.push(answer[column.name]);
                        } else {
                            row.fields.push('');
                        }
                    }

                    $scope.rows.push(row);
                }
            })
    };

    $scope.fetchFields = function fetchFields(){
        $http.get('/get_unique_keys/')
            .success(function(data){
                $scope.fields = data;
                $scope.columns = $scope.fields;
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

            url += data[x];
        }

        url += ']';

        window.location.assign(url);
    };

    $scope.fetchFields();

});