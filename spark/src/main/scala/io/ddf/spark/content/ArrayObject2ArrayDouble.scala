package io.ddf.spark.content

import org.apache.spark.rdd.RDD
import io.ddf.content.{Representation, ConvertFunction}
import io.ddf.DDF
import io.ddf.exception.DDFException

/**
  */
class ArrayObject2ArrayDouble(@transient ddf: DDF) extends ConvertFunction(ddf) with ObjectToDoubleMapper {

  override def apply(representation: Representation): Representation = {
    representation.getValue match {
      case rdd: RDD[Array[Object]] => {
        val mappers = getMapper(ddf.getSchemaHandler.getColumns)
        val rddArrDouble = rdd.map {
          array => {
            val arr = new Array[Double](array.size)
            var i = 0
            var isNULL = false
            while ((i < array.size) && !isNULL) {
              mappers(i)(array(i)) match {
                case Some(number) => arr(i) = number
                case None => isNULL = true
              }
              i += 1
            }
            if (isNULL) null else arr
          }
        }.filter(row => row != null)
        new Representation(rddArrDouble, RepresentationHandler.RDD_ARR_DOUBLE.getTypeSpecsString)
      }
      case _ => throw new DDFException("Error getting RDD[Array[Double]]")
    }
  }
}
