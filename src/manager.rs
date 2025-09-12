#[path="grid.rs"]
pub mod grid;
pub use grid::*;
use pyo3::{prelude::*};

#[pyclass(module = "ccbenchmark")]
pub struct Manager {
    base_value_grids: Vec<Grid>,
    output_grid: Grid,
    comparison_grid: Grid
}

#[pyclass(module = "ccbenchmark", get_all, set_all)]
pub struct Profile {
    pub selected_indicies: Vec<usize>,
    pub unit: String
}

#[pymethods]
impl Manager {
    #[new]
    pub fn new() -> Self {
        Self { 
            base_value_grids: Vec::new(), 
            output_grid: Grid::new(Unit::PureUnit(PureUnit::NoUnit), 0, 0), 
            comparison_grid: Grid::new(Unit::PureUnit(PureUnit::NoUnit), 0, 0) 
        }
    }
    pub fn emplace(&mut self, metric_count: usize, iteration_count: usize, unit_str: String) {
        let unit = Unit::from_str(&unit_str);
        self.base_value_grids.push(Grid::new(unit, iteration_count, metric_count));
    }

    fn update_unit_comparison_grid(&mut self, profile: &Profile) {
        let compare_func = |base: f64, other: f64| {
            let div = other / base;
            (div - 1.0) * 100.0
        };
        if profile.selected_indicies.len() == 1 {
            let index = profile.selected_indicies[0];
            debug_assert!(index < self.base_value_grids.len());
            let base_grid = &self.base_value_grids[index];
            let unit = Unit::from_str(&profile.unit);
            self.output_grid = base_grid.clone_convert_unit(&unit).unwrap();
            self.comparison_grid = base_grid.clone_compare_neighbors(compare_func, Unit::PureUnit(PureUnit::Percentage));
        }
        else if profile.selected_indicies.len() > 1 {
            let col_count = self.base_value_grids[0].column_count();
            let unit = Unit::from_str(&profile.unit);
            self.output_grid = Grid::new(unit, profile.selected_indicies.len(), col_count);

            for (to_index, sel_index) in profile.selected_indicies.iter().enumerate() {
                let sel_grid = &self.base_value_grids[*sel_index];
                if let Some(recent_index)= sel_grid.back_col_index() {
                    for col_index in 0..col_count {
                        debug_assert!(col_index < sel_grid.column_count(), "i: {}, {} < {}", *sel_index, col_index, sel_grid.column_count());
                        debug_assert!(recent_index < sel_grid.column_length(), "i: {}, {} < {}", *sel_index, recent_index, sel_grid.column_length());

                        let value = sel_grid.get(col_index, recent_index);
                        self.output_grid.set(col_index, to_index, value, sel_grid.unit());
                    }
                }
            }
            let compare_index = 0;
            self.comparison_grid = self.output_grid.clone_compare_index(compare_func, Unit::PureUnit(PureUnit::Percentage), compare_index);
        }
    }
    fn get_matrix_as_str(&mut self) -> Vec<Vec<String>> {
        let col_count = self.output_grid.column_count();
        let col_len = self.output_grid.column_length();

        let out_unit = self.output_grid.unit().as_str();
        let comp_unit = self.comparison_grid.unit().as_str();

        let mut matrix_str: Vec<Vec<String>> = vec![vec!["".to_string();col_len];col_count*2];
        for i in 0..col_count {
            let out_column = self.output_grid.column(i);
            let mut to_index = i*2;
            for (j, out_value) in out_column.iter().enumerate() {
                matrix_str[to_index][j] = format!("{:.2} {}", *out_value, out_unit);
            }
            to_index += 1;
            let comp_column = self.comparison_grid.column(i);
            for (j, comp_value) in comp_column.iter().enumerate() {
                matrix_str[to_index][j] = format!("{:.2} {}", *comp_value, comp_unit);
            }
        }
        print!("Str, Col Count: {}, Col Len: {}", matrix_str.len(), matrix_str[0].len());
        matrix_str
    }
    pub fn run_profile(&mut self, profile: &Profile) -> Vec<Vec<String>> {
        self.update_unit_comparison_grid(profile);
        self.get_matrix_as_str()
    }
    
    pub fn set(&mut self, benchmark_index: usize, metric_index: usize, iteration_index: usize, value: f64, unit_str: String) {
        let unit = Unit::from_str(&unit_str);
        self.base_value_grids[benchmark_index]
            .set(metric_index, iteration_index, value, unit);
    }
}

impl Manager {
    pub fn push(&mut self, grid: Grid) {
        self.base_value_grids.push(grid);
    }
    pub fn set_grid(&mut self, index: usize, grid: Grid) {
        self.base_value_grids[index] = grid
    }
}