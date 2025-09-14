pub mod manager;
#[allow(unused_imports)]
pub use manager::*;
use pyo3::prelude::*;

#[pymodule]
fn _ccbenchmark(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Manager>()?;
    m.add_class::<Profile>()?;

    Ok(())
}