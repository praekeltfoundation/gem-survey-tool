var gems = angular.module('gems');

gems.controller('queryController', function($scope, $http){

    $scope.fields = [];

    $scope.operators = [
        {name: 'Less than', operator: 'lt'},
        {name: 'Less than or equal to', operator: 'lte'},
        {name: 'Greater than', operator: 'gt'},
        {name: 'Greater than or equal to', operator: 'gte'},
        {name: 'Equal to', operator: 'eq'},
        {name: 'Text contains', operator: 'co'},
        {name: 'Not equal to', operator: 'neq'},
        {name: 'Text does not contain', operator: 'nco'},
        {name: 'Text is exactly', operator: 'ex'},
    ];

    $scope.queryWords = '';

    /*
    $scope.filters = [
        {
            "field": {
                "type": "N",
                "name": "contact"
            },
            "filters": [
                {
                    "operator": "lt",
                    "value": "18"
                },
                {
                    "loperator": "or",
                    "operator": "gt",
                    "value": "12"
                }
            ]
        },
        {
            "loperator": "or",
            "field": {
                "type": "N",
                "name": "survey"
            },
            "filters": [
                {
                    "operator": "eq",
                    "value": "female"
                }
            ]
        }
    ];
    */

    //$scope.filters = $scope.groupFilter;

    $scope.queryWordOperator = function queryWordOperator(op){
        var retVal = '';

        if(op == 'lt'){
            retVal = '<';
        }
        else if(op == 'lte'){
            retVal = '<=';
        }
        else if(op == 'gt'){
            retVal = '>';
        }
        else if(op == 'gte'){
            retVal = '>=';
        }
        else if(op == 'eq' || op == 'ex'){
            retVal = 'equals';
        }
        else if(op == 'co'){
            retVal = 'contains';
        }
        else if(op == 'neq'){
            retVal = 'not equals';
        }
        else if(op == 'nco'){
            retVal = 'not contains';
        }

        return retVal;
    };

    $scope.fetchFields = function fetchFields(){
        $http.get('/get_unique_keys/')
            .success(function(data){
                $scope.fields = $scope.cleanFields(data);
                $scope.columns = $scope.fields;
                $scope.processFilters();
            })
    };

    $scope.addFilter = function addFilter(){
        $scope.filters.push(
            {
                loperator: "and",
                field:null,
                filters: [{loperator: null, operator: null, value: null}]
            })
    };

    $scope.addFieldFilter = function addFieldFilter(pIndex){
        $scope.filters[pIndex].filters.push({loperator: 'and', operator: null, value: null});
    };

    $scope.removeFieldFilter = function removeFieldFilter(pIndex, index){
        $scope.filters[pIndex].filters.splice(index, 1);
    };

    $scope.removeFilter = function removeFilter(pIndex){
        $scope.filters.splice(pIndex, 1);
    }

    $scope.processFilters = function processFilters(){
        for(var x = 0; x < $scope.filters.length; ++x){
            for(var y = 0; y < $scope.fields.length; ++y){
                if($scope.filters[x].field.name == $scope.fields[y].name){
                    $scope.filters[x].field = $scope.fields[y];
                }
            }
        }
    };

    $scope.makeQueryWords = function makeQueryWords(){
        var words = '';

        for(var x = 0; x < $scope.filters.length; ++x){
            var filter = $scope.filters[x];
            var field = filter.field;

            if(x > 0){
                words += ' ' + filter.loperator + ' ';
            }

            if(filter.filters.length > 1){
                words += '( ';
            }

            for(var y = 0; y < filter.filters.length; ++y){
                if(y > 0){
                    words += ' ' + filter.filters[y].loperator + ' ';
                }
                words += field.name + ' ' + $scope.queryWordOperator(filter.filters[y].operator) + ' ' + filter.filters[y].value;
            }

            if(filter.filters.length > 1){
                words += ' )';
            }
        }

        $scope.queryWords = words;
    };

    $scope.fetchFields();
    $scope.makeQueryWords();

    $scope.$watch('filters', function(){
       $scope.makeQueryWords();
    }, true);
});