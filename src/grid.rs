#[path ="unit.rs"]
pub mod unit;
pub use unit::*;

#[derive(Clone)]
pub struct Grid {
    entries: Vec<f64>,
    unit: Unit,

    column_length: usize,
    column_count: usize
}

#[allow(dead_code)]
impl Grid {
    pub fn new(unit: Unit, column_length: usize, column_count: usize) -> Self {
        Self { entries: vec![f64::NAN; column_length*column_count], unit, column_length, column_count }
    }

    pub fn column(&self, col_index: usize) -> &[f64] {
        let from = col_index*self.column_length;
        let to = from+self.column_length;
        let slice = &self.entries[from..to];
        slice
    }

    pub fn set_column(&mut self, col_index: usize, other: &[f64], unit: Unit) -> &mut Self {
        let translation_scaler = self.unit.as_scaler()/unit.as_scaler();
        let translated_values: Vec<f64> = (0..other.len()).map(|i| other[i]*translation_scaler).collect();

        let from = col_index*self.column_length;
        let to = from+self.column_length;
        let slice = &mut self.entries[from..to];
        slice.copy_from_slice(translated_values.as_slice());
        self
    }

    pub fn get(&self, col_index: usize, index: usize) -> f64 {
        self.entries[col_index*self.column_length + index]
    }

    pub fn set(&mut self, col_index: usize, index: usize, value: f64, unit: Unit) -> &mut Self {
        let translation_scaler = self.unit.as_scaler()/unit.as_scaler();
        let translated_value = value*translation_scaler;
        self.entries[col_index*self.column_length + index] = translated_value;
        self
    }

    pub fn unit(&self) -> Unit {
        self.unit.clone()
    }

    pub fn len(&self) -> usize {
        self.entries.len()
    }

    pub fn column_length(&self) -> usize {
        self.column_length
    }

    pub fn column_count(&self) -> usize {
        self.column_count
    }

    pub fn clone_convert_unit(&self, unit: &Unit) -> Option<Self> {
        if !self.unit.same_unit_pattern(unit) {
            return None
        }
        let mut new_grid = Self::new(unit.clone(),self.column_length, self.column_count);
        let translation_scaler = self.unit.as_scaler()/unit.as_scaler();
        for (i, entry) in self.entries.iter().enumerate() {
            new_grid.entries[i] = *entry * translation_scaler;
        }
        Some(new_grid)
    }

    pub fn front_col_index(&self) -> Option<usize> {
        for front_index in 0..self.column_length {
            for i in 0..self.column_count {
                if !self.column(i)[front_index].is_nan() {
                    return Some(front_index)
                }
            }
        }
        None
    }
    pub fn back_col_index(&self) -> Option<usize> {
        for back_index in (0..self.column_length).rev() {
            for i in 0..self.column_count {
                if !self.column(i)[back_index].is_nan() {
                    return Some(back_index)
                }
            }
        }
        None
    }

    pub fn clone_compare_neighbors<CompareF>(&self, compare_func: CompareF, unit: Unit) -> Self where 
        CompareF: Fn(f64, f64) -> f64 {
        
        let mut output_grid: Grid = Self::new(unit, self.column_length, self.column_count);
        let mut entry_index: usize = 0;

        for _ in 0..self.column_count {
            let mut previous_index: usize = entry_index;
            entry_index += 1;
            for _ in 1..self.column_length {
                let base = self.entries[previous_index];
                let other = self.entries[entry_index];

                output_grid.entries[entry_index] = compare_func(base, other);

                if !other.is_nan() {
                    previous_index = entry_index
                }
                entry_index += 1;
            }
        }

        output_grid
    }

    pub fn clone_compare_index<CompareF>(&self, compare_func: CompareF, unit: Unit, index: usize) -> Self where 
        CompareF: Fn(f64, f64) -> f64 {
        
        let mut output_grid = Self::new(unit, self.column_length, self.column_count);
        let mut entry_index: usize = 0;

        if index >= self.column_length {
            return output_grid
        }

        for column_index in 0..self.column_count {
            let column = self.column(column_index);
            let base = column[index];
            for _ in 0..self.column_length {
                let other = self.entries[entry_index];
                output_grid.entries[entry_index] = compare_func(base, other);

                entry_index += 1;
            }
        }

        output_grid
    }
}